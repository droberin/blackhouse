from flask import Flask, jsonify, request, Response
from functools import wraps
from blackhouse.flat_configuration import BlackhouseConfiguration, GPIODeviceConfiguration
from time import sleep

import json
import os.path
import logging
from os import getenv

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
app = Flask(__name__, static_url_path='/static')
app.config.from_object(__name__)

cfg = BlackhouseConfiguration()

users_file = cfg.config_structure['blackhouse_configuration_directory'] + '/' + cfg.config_structure['users_file']

blackhouse_service_type = getenv('BH_SERVICE_TYPE', 'controller')
print("Local device is running as: {}".format(blackhouse_service_type))
if blackhouse_service_type == 'push':
    print("Device is PUSH. Trying to load GPIO.")
    import RPi.GPIO as GPIO


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    if not os.path.isfile(users_file):
        logging.info("No users config file found. You should create one if you wanna use this in production.")
        if username == 'admin' and password:
            logging.info("Generating user admin with requested password...")
            generation_report = generate_basic_user_file(password)
    try:
        with open(users_file) as data_file:
            data = json.load(data_file)
            if username in data:
                return password == data[username]
            else:
                return False
    except FileNotFoundError:
        logging.info("No users file seem to be available")


def generate_basic_user_file(password, force=False):
    my_response = False
    default_file_content = '{"admin": "' + password + '"}'
    if os.path.isfile(users_file):
        if not force:
            my_response = False
    else:
        with open(users_file, "w") as my_users_file:
            my_users_file.write(default_file_content)
            my_users_file.close()
            if my_users_file:
                my_response = True
    return my_response


# TODO: elaborate from this...
def check_auth_by_token(token):
    """
    This function is called to check if a token is valid
    """
    return token == 'CRAZYTOKEN'


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/')
@app.route('/index.html')
@requires_auth
def index():
    my_welcome = {
        "tag": "willkomen",
        'object1': True if os.path.isfile('/.docker') else False
    }
    return jsonify(my_welcome)


@app.route('/push/<int:my_switch>', methods=['PUT'])
@requires_auth
def set_push_button(my_switch):
    if GPIODeviceConfiguration().valid_pin(my_switch):
        try:
            temp_switch = set_gpio_status(my_switch)
            return temp_switch
        except (KeyError, TypeError):
            return jsonify("Missing status request")
    return jsonify("No valid push button specified")


@app.route('/switch/<string:my_switch>', methods=['GET'])
@requires_auth
def get_switch(my_switch):
    if GPIODeviceConfiguration().valid_pin(my_switch):
        temp_switch = get_gpio_status(my_switch)
        switch_status = {
            'status': temp_switch,
        }
        return jsonify(switch_status)


def get_gpio_status(gpio_pin):
    # GPIO.setmode(GPIO.BCM)
    # GPIO.setup(gpio_pin, GPIO.OUT)
    return '{"state":"' + str(1) + '"}'


def set_gpio_status(gpio_pin, duration=2):
    logging.info("pushing pin {} for {} seconds".format(gpio_pin, duration))
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(gpio_pin, GPIO.OUT)
    GPIO.output(gpio_pin, GPIO.LOW)
    sleep(0.5)
    GPIO.output(gpio_pin, GPIO.HIGH)
    sleep(duration)
    GPIO.output(gpio_pin, GPIO.LOW)
    GPIO.cleanup()
    return '{"state":"done","pin":"' + str(gpio_pin) + '"}'


if __name__ == "__main__":
    cfg = BlackhouseConfiguration()
    certificate_file = cfg['blackhouse_configuration_directory'] + '/ssl/cert.pem'
    certificate_key = cfg['blackhouse_configuration_directory'] + '/ssl/cert.key'
    if os.path.isfile(certificate_file) and os.path.isfile(certificate_key):
        logging.info("Certificates found. Trying to run in SSL mode")
        # order matters
        context = (certificate_file, certificate_key)
        app.run(debug=False, host="0.0.0.0", ssl_context=context, port=5003)
    else:
        logging.info("No certificates found in SSL configuration folder. Running insecure socket mode")
        app.run(debug=False, host="0.0.0.0", port=5002)
