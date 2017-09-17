# -*- coding: utf-8 -*-
import requests
import logging


class GPIOSwitch:
    config = None

    def __init__(self, config):
        self.config = config

    def state(self):
        return False

    def name(self):
        if self.config['name']:
            return self.config['name']
        else:
            return "unknown"

    def turn_on(self, pin):
        pass

    def turn_off(self, pin):
        pass

    def toggle(self, pin):
        pass

    def push(self, pin):
        try:
            request_url = self.config['proto'] + '://' + self.config['username'] + ':' + self.config['password'] + '@' \
                          + self.config['hostname'] + ':' + str(self.config['port']) + '/push/' + str(pin)
            logging.debug("PUSH requested to {}".format(request_url))
            my_request = requests.put(request_url, data='{"status": "on"}')
            logging.debug("Request status code: {}".format(my_request.status_code))
        except KeyError as e:
            logging.error("GPIOSwitch: not properly configured. Missing key: {}".format(e))
