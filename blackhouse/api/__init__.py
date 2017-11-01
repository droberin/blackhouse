from flask import Flask, jsonify, request, Response, render_template, abort
import requests
from functools import wraps
# from blackhouse import arcade
from pyHS100.pyHS100 import SmartPlug
from blackhouse.flat_configuration import BlackhouseConfiguration

import json
import os.path
import logging
from os import getenv

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
app = Flask(__name__, static_url_path='/static')
app.config.from_object(__name__)

blackhouse_config_instance = BlackhouseConfiguration()

blackhouse_configuration_directory = blackhouse_config_instance.config_structure['blackhouse_configuration_directory']
users_file = blackhouse_configuration_directory + '/' + blackhouse_config_instance.config_structure['users_file']

blackhouse_switches_config =\
    blackhouse_configuration_directory + '/'\
    + blackhouse_config_instance.config_structure['blackhouse_configuration_devices']

blackhouse_service_type = getenv('BH_SERVICE_TYPE', 'controller')
from blackhouse.switch.gpioswitch import GPIOSwitch

current_user = None


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    global current_user
    if not os.path.isfile(users_file):
        logging.info("No users.json config file found. You should create one if you wanna use this in production.")
        if username == 'admin' and password:
            logging.info("Generating user admin with requested password...")
            generation_report = generate_basic_user_file(password)
    try:
        with open(users_file) as data_file:
            data = json.load(data_file)
            if username in data:
                current_user = username
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


def provide_valid_file_or_fail(file):
    valid_static_files = [
        'angular.min.js',
        'angular.min.js.map',
        'protractor.js',
        'materialize.js',
        'materialize.min.js',
        'materialize.css',
        'materialize.min.css',
        'test.html',
        'animation.css',
        'style.css',
        'bootstrap.min.css',
        'Roboto-Regular.woff',
        'Roboto-Regular.woff2',
        'Roboto-Bold.woff',
        'Roboto-Bold.woff2',
        'Roboto-Light.woff2',
        'Roboto-Light.woff',
        'depuradora.jpg',
        'ventilador.jpg',
        'generic.jpg',
        'push.png',
        'gate.png',
    ]
    extension_folder_dict = {
        '.html': 'html',
        '.js': 'js',
        '.css': 'css',
        '.jpg': 'images',
        '.png': 'images',
        '.ogv': 'video',
        '.ogg': 'audio',
        '.svg': 'images',
        '.woff': 'fonts',
        '.woff2': 'fonts',
    }
    file = os.path.split(file)[1]
    if file not in valid_static_files:
        if not file.endswith('.jpg') and not file.endswith('.gif') and not file.endswith('.png'):
            return None
    for extension in extension_folder_dict:
        if file.endswith(extension):
            return extension_folder_dict.get(extension) + '/' + file
    return None


def dockerised():
    return True if os.path.isfile('/.dockerenv') else False

# Alias for USA
dockerized = dockerised


def template(template_name):
    """
    Returns file from Jinja2 template
    :param template_name: name of the template
    :return:
    """
    valid_templates = {
        'index': 'index.html'
    }
    if valid_templates.get(template_name):
        configuration = BlackhouseConfiguration()
        devices = configuration.devices
        logging.debug('Devices used in template "{}":'.format(template_name))
        return render_template(
            template_name + '.html',
            devices=devices,
            dockerised=dockerised(),
            logged_user=current_user,
        )
    else:
        logging.debug('Template {} not found'.format(template_name))
        return jsonify("Sorry, can't find that template")


def request_push_to_device(my_switch, switch_type, my_pin):
    """
    Push only, can be used from CLI.
    :param my_switch: switch name defined in devices configuration
    :param switch_type: gpio_push
    :param my_pin: pin int.
    :return: result of execution or False
    """
    configuration = BlackhouseConfiguration()
    if not configuration.get_devices(switch_type):
        return False
    service = configuration.get_device_info(my_switch, switch_type)
    if service:
        if switch_type == "gpio_push":
            temp_switch = GPIOSwitch(service)
            return temp_switch.push(my_pin)
        else:
            return "Missing valid device"
    logging.debug("Service not Found: {}".format(service))
    return service


@app.route('/js/<path:path>')
@app.route('/css/<path:path>')
@app.route('/html/<path:path>')
@app.route('/audio/<path:path>')
@app.route('/video/<path:path>')
@app.route('/images/<path:path>')
@app.route('/fonts/roboto/<path:path>')
@app.route('/fonts/<path:path>')
@requires_auth
def validate_static_content(path):
    file = provide_valid_file_or_fail(path)
    if file:
        if os.path.isfile(app.static_folder + '/' + file):
            return app.send_static_file(file)
        # If content is not found, print a warning
        logging.warning("Static content requested but not found: {}".format(file))
    # Defaults to 404
    abort(404)


@app.route('/api/welcome')
@app.route('/welcome.htm')
@app.route('/api/buttons')
def welcome_message():
    my_welcome = {
        "tag": "willkomen",
        'object1': True if os.path.isfile('/.docker') else False
    }
    return jsonify(my_welcome)


@app.route('/')
@app.route('/index')
@requires_auth
def index():
    return template('index')
    # return app.send_static_file('index.html')


@app.route('/switch/<string:switch_type>/<string:my_switch>', methods=['PUT'])
@requires_auth
def set_switch(switch_type, my_switch):
    configuration = BlackhouseConfiguration()
    if not configuration.get_devices(switch_type):
        return jsonify(False)
    service = configuration.get_device_info(my_switch)
    if service:
        if switch_type == "hs100":
            temp_switch = SmartPlug(service['hostname'])
        elif switch_type == "gpio_switch":
            temp_switch = GPIOSwitch(service)
        else:
            return jsonify("Missing valid device")
        # switch_status = {
        #     'status': temp_switch.state,
        #     'alias': temp_switch.alias
        # }
        data = request.get_json()
        try:
            if data['status'] == "on" or data['status'] == "true":
                temp_switch.turn_on()
                return jsonify(temp_switch.state)
            elif data['status'] == "off" or data['status'] == "false":
                temp_switch.turn_off()
                return jsonify(temp_switch.state)
            elif data['status'] == "toggle":
                temp_switch.turn_on()
            else:
                return jsonify("Unknown state requested, br0")
        except (KeyError, TypeError):
            return jsonify("Missing status request")
    return jsonify(service)


@app.route('/push/<string:switch_type>/<string:my_switch>/<string:my_pin>', methods=['PUT'])
@requires_auth
def push_switch(switch_type, my_switch, my_pin):
    return jsonify(request_push_to_device(my_switch, switch_type, my_pin))


@app.route('/switch/<string:switch_type>/<string:my_switch>', methods=['GET'])
@requires_auth
def get_switch(switch_type, my_switch):
    configuration = BlackhouseConfiguration()
    if not configuration.get_devices(switch_type):
        return jsonify(False)
    service = configuration.get_device_info(my_switch)
    if service:
        if switch_type == "hs100":
            temp_switch = SmartPlug(service['hostname'])
            switch_status = {
                'status': temp_switch.state,
                'alias': temp_switch.alias,
            }
            return jsonify(switch_status)
        elif switch_type == "gpio_push":
            temp_switch = GPIOSwitch(service)
            switch_status = {
                'status': temp_switch.state(),
                'alias': temp_switch.name(),
            }
            return jsonify(switch_status)
        else:
            return jsonify(message="Switch not found or incorrect")


if __name__ == "__main__":
    certificate_file = blackhouse_configuration_directory + '/ssl/cert.pem'
    certificate_key = blackhouse_configuration_directory + '/ssl/cert.key'
    if os.path.isfile(certificate_file) and os.path.isfile(certificate_key):
        logging.info("Certificates found. Trying to run in SSL mode")
        # order matters
        context = (certificate_file, certificate_key)
        app.run(debug=False, host="0.0.0.0", ssl_context=context, port=5001)
    else:
        logging.info("No certificates found in SSL configuration folder. Running insecure socket mode")
        app.run(debug=False, host="0.0.0.0", port=5000)
