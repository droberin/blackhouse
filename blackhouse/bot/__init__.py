from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

import os
import sys
import time
import logging
from time import gmtime, strftime
import datetime
import pyotp
import json
from blackhouse.tools import wake_on_lan
import getopt
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

from blackhouse.flat_configuration import BlackhouseConfiguration
from blackhouse.switch.gpioswitch import GPIOSwitch

debug = True

token_file = ".token_secret"

token_file_full_path = None
config_file_full_path = None

my_token = os.getenv('TELEGRAM_TOKEN', None)

# Check if running inside a Docker container
if os.path.isfile("/.dockerenv"):
    config_dir = os.getenv('TELEGRAM_CONFIG_DIR', "/app/etc")
    running_in_docker = True
else:
    config_dir = os.getenv('TELEGRAM_CONFIG_DIR', ".")
    running_in_docker = False

try:
    opts, args = getopt.getopt(
        sys.argv[1:],
        "hdt:u:c:",
        ["debug","token-file=","users-file=","computers-file=","config-dir=","cd="]
    )
except getopt.GetoptError:
    print(sys.argv[0] + ' -u <users_file> -c <computers_file> -t <token_file>')
    sys.exit(2)

for opt, arg in opts:
    if opt == '-h':
        print(sys.argv[0] + ' -u <users_file> -c <computers_file> -t <token_file>')
        sys.exit(0)
    elif opt in ("-d", "--debug"):
        logging.info("Requested log level change to DEBUG.")
        logging.getLogger().setLevel(logging.DEBUG)
    elif opt in ("-t", "--token-file"):
        token_file_full_path = arg
        logging.debug("Token full path set to {}".format(token_file_full_path))
    elif opt in ("-u", "--users-file"):
        config_file_full_path = arg
        logging.debug("Config file (users) full path set to {}".format(config_file_full_path))
    elif opt in ("--cd", "--config-dir"):
        config_dir = arg
        logging.debug("Configuration directory set to {}".format(config_dir))


if my_token is None:
    if not token_file_full_path:
        token_file_full_path = config_dir + "/" + token_file
    if os.path.isfile(token_file_full_path):
        logging.debug("Token file found, trying to load it.")
        with open (token_file_full_path, "r") as my_config:
            my_token = my_config.read(50).rstrip(os.linesep)
    else:
        logging.error("No token file found in {}".format(token_file_full_path))
        sys.exit(1)
else:
    logging.info("Got token from environment")

try:
    updater = Updater(token=my_token)
    dispatcher = updater.dispatcher
except:
    logging.error("Token error")
    sys.exit(2)
finally:
    logging.debug("End of token load process")

if not config_file_full_path:
    config_file_full_path = config_dir + "/config.json"
if os.path.isfile(config_file_full_path):
    valid_uids = json.load(open(config_file_full_path))
    # Please, avoid this, might have passwords os suff you don't want to see
    # logging.debug(valid_uids)
else:
    # Fail if no config is found
    if not running_in_docker:
        logging.error("Configuration not found at {}".format(config_file_full_path))
        sys.exit(1)
    else:
        if os.path.isfile(config_file_full_path + ".example"):
            logging.warning("No configuration file found at {} but example is..."
                            " loading it. FIX THIS!".format(config_file_full_path))
            valid_uids = json.load(open(config_file_full_path + ".example"))
        else:
            logging.error("Configuration not found at {}".format(config_file_full_path))
            sys.exit(1)


computers_file_full_path = config_dir + "/config.computers.json"
known_computers = None

if os.path.isfile(computers_file_full_path):
    if running_in_docker:
        logging.warning(
            "This bot is running as a Docker container,"
            " so it might be unable to wake or reach any computer"
        )
    known_computers = json.load(open(computers_file_full_path))
    logging.debug(known_computers)
else:
    if not running_in_docker:
        logging.error("Computers configuration not found at {}".format(computers_file_full_path))
        sys.exit(1)
    else:
        if os.path.isfile(computers_file_full_path + ".example"):
            logging.info("No computer configuration file found at {} but example is..."
                         "loading it. FIX THIS!".format(computers_file_full_path + ".example"))
            valid_uids = json.load(open(computers_file_full_path + ".example"))
        else:
            logging.error("Computer Configuration not found at {}".format(computers_file_full_path))
            sys.exit(1)


def start(bot, update):
    bot.sendMessage(
        chat_id=update.message.chat_id,
        text="Hi, {}, here I am.\n"
             "Tell me what you want!\n"
             "\n"
             "Perhaps a /help will be handy [TODO]\n"
             "Userful commands:\n"
             "\topen: to open a gate\n"
             "\ttotp: provides a OTP code you can give to someone at the entrance\n"
             "\ttoggle: toggles a gate\n"
             "".format(update.message.chat.username)
    )
    logging.info("[START] ID {} requested a start (@{})".format(update.message.chat_id, update.message.chat.username))

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


def open_door(bot, update):
    chat_id = update.message.chat_id
    if update.message.chat_id in valid_uids:
        username = valid_uids[update.message.chat_id]['name']
        bot.sendMessage(chat_id=chat_id, text="Para ti sí, {}.".format(username))
        logging.info("[{}] Opening door for '{}'".format(chat_id, username))
    else:
        bot.sendMessage(chat_id=update.message.chat_id, text="Not for you, incognito. {}".format(update.message.chat_id))


open_handler = CommandHandler('abrir', open_door)
dispatcher.add_handler(open_handler)


def echo(bot, update):
    global valid_uids
    global known_computers

    chat_id = str(update.message.chat_id)
    message = update.message.text
    incoming_photos = update.message.photo
    message_time = update.message.date
    current_time = datetime.datetime.fromtimestamp(time.time())
    diff_time = current_time - message_time
    full_name = update.message.chat.first_name + " " + update.message.chat.last_name
    user_name = update.message.chat.username
    logging.debug("DEBUG: echo(): chat_id: {} [@{}] [Photos: {}]".format(chat_id, user_name, len(incoming_photos)))

    if diff_time.seconds > 10:
        logging.warning("[IGNORED] Old message ({}) has been received from {} [{}]"
                        "\n\tReachable through [ http://t.me/{} or tg://resolve?domain={} ]".format(
                            update.message.date,
                            chat_id,
                            full_name,
                            user_name,
                            user_name))
        return False
    if len(incoming_photos) > 0:
        logging.info("Some photos are coming!!! {}".format(len(incoming_photos)))

    if message.lower().startswith("configure"):
        if chat_id in valid_uids:
            params = message.split(' '),
            params = params[0]
            if len(params) > 1:
                if params[1] == "phone":
                    if len(params) > 2:
                        logging.info("[{}] configured a new phone number.".format(chat_id))
                        current_phone_number = valid_uids[chat_id]['phone']
                        bot.sendMessage(chat_id=chat_id, text="Cambiado teléfono de '{}' a '{}'"
                                        .format(current_phone_number, params[2]))
                        valid_uids[chat_id]['phone'] = params[2]
                    else:
                        bot.sendMessage(chat_id=chat_id, text="Prueba a añadir también el número.")
                elif params[1] == "name":
                    bot.sendMessage(chat_id=chat_id, text="No, no te dejo cambiarte el nombre. Te llamas {} y punto"
                                    .format(valid_uids[chat_id]['name']))
                else:
                    bot.sendMessage(chat_id=chat_id, text="No sé qué hacer con eso. {}".format(params))
            else:
                bot.sendMessage(chat_id=chat_id, text="Erm no idea {}".format(len(params)))
        else:
            bot.sendMessage(chat_id=chat_id, text="Que a ti ni agua.")

    elif message.lower().startswith("hi") or message.lower().startswith("hola"):
        if chat_id in valid_uids:
            bot.sendMessage(chat_id=chat_id, text="Hi, {}".format(user_name))
        else:
            bot.sendMessage(chat_id=chat_id, text="Hola, persona desconocida que se hace llamar «{}»".format(user_name))

    elif message.lower().startswith("gate") or\
            message.lower().startswith("puerta"):
        if chat_id in valid_uids:
            configuration = BlackhouseConfiguration()
            if not configuration.get_devices('gpio_push'):
                bot.sendMessage(chat_id=chat_id, text="Coudn't find any GPIO_push device")
                return False
            service = configuration.get_device_info('gate')
            if service:
                temp_switch = GPIOSwitch(service)
                temp_switch.push(18)
            else:
                bot.sendMessage(chat_id=chat_id, text="No 'gpio_push' device named 'gate' found. (PIN 18)")
        else:
            bot.sendMessage(chat_id=chat_id, text="Ya te molaba.\nHabla con el superintendente para que te dé acceso\n"
                                                  "Tu ID es: {}".format(chat_id))
    elif message.lower().startswith("time"):
        showtime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        bot.sendMessage(chat_id=chat_id, text="GMT: {}".format(showtime))

    elif message.lower().startswith("totp"):
        if chat_id in valid_uids:
            if "totp_key" in valid_uids[chat_id]:
                totp = pyotp.TOTP(valid_uids[chat_id]['totp_key'])
                current_pass = totp.now()
                bot.sendMessage(chat_id=chat_id, text="Current pass: {}".format(current_pass))
            else:
                bot.sendMessage(chat_id=chat_id, text="Don't know your key... Sorry")
        else:
            logging.info("Unknown user: {}".format(chat_id))
            bot.sendMessage(chat_id=chat_id, text="Don't know you.")

    elif message.lower().startswith("reload"):
        return_message = str()
        if os.path.isfile(config_file_full_path):
            valid_uids = json.load(open(config_file_full_path))
            return_message += "[Users]: Loaded {}\n".format(config_file_full_path)
        else:
            return_message += "No configfile {} found\n".format(config_file_full_path)

        if os.path.isfile(computers_file_full_path):
            known_computers = json.load(open(computers_file_full_path))
            return_message += "[Computers]: Loaded {}\n".format(computers_file_full_path)
        else:
            return_message += "No computersfile {} found\n".format(computers_file_full_path)
        bot.sendMessage(chat_id=chat_id, text=return_message)

    elif message.lower().startswith("wol") or message.lower().startswith("wake"):
        if chat_id in valid_uids:
            params = message.split(' '),
            params = params[0]
            if len(params) > 1:
                if params[1]:
                    computer = params[1]
                    if computer in known_computers:
                        if "mac" in known_computers[computer]:
                            mac_address = known_computers[computer]['mac']
                            logging.info("Waking up computer {} [{}]".format(computer, mac_address))
                            bot.sendMessage(chat_id=chat_id, text="Machine '{}' found. "
                                                                  "Requesting Wake On Lan".format(computer))
                            try:
                                wake_on_lan(mac_address)
                            finally:
                                pass
                        else:
                            bot.sendMessage(chat_id=chat_id, text="Machine found but no 'mac' address found, sorry")
                    else:
                        bot.sendMessage(chat_id=chat_id, text="Machine not found in list")
                else:
                    bot.sendMessage(chat_id=chat_id, text="¿Qué máquina?")
            else:
                bot.sendMessage(chat_id=chat_id, text="Erm no idea [{}]".format(len(params)))
        else:
            logging.info("[WOL] Unknown user: {} [@{} ]".format(chat_id, user_name))
            bot.sendMessage(chat_id=chat_id, text="Don't know you.")
    elif message.startswith("whoami"):
        bot.sendMessage(chat_id=chat_id, text="Eres: {}".format(chat_id))
    else:
        bot.sendMessage(chat_id=chat_id, text="No he entendido guay. Comienza nuevamente el proceso")


updater.start_polling()
echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)

updater.idle()
