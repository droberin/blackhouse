import logging


def __get_arcade_address():
    return "192.168.1.20"


# Arcade restart
def restart(method='MQTT'):
    if method is 'MQTT':
        logging.info("Restart vía MQTT")
    else:
        arcade_address = __get_arcade_address()
        logging.info("Restarting Arcade at {}".format(arcade_address))


def start():
    logging.info("Starting Arcade vía MQTT")


def stop():
    logging.info("Stopping Arcade vía MQTT")
