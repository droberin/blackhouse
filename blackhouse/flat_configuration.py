import logging
import os
import configobj


class BlackhouseConfiguration:
    config_structure = None
    devices = {
        "hs100": dict(),
        "gpio_switches": dict(),
    }
    config_file = None

    def __init__(self):
        self.reload()

    def reload(self):
        devices_file = self.config_structure['blackhouse_configuration_devices']
        if devices_file and os.path.isfile(devices_file):
            raw_devices = configobj.ConfigObj(devices_file)
            return_default = True
            if len(raw_devices) > 0:
                for device in raw_devices:
                    try:
                        if device['type'].lower() == "hs100":
                            self.devices['hs100'][device] = raw_devices[device]
                        else:
                            logging.warning("Device type '{}' unknown for device '{}'".format(device['type'], device))
                    except KeyError:
                        logging.warning("Device {} can't be configured. Check config file.".format(device))
                        return_default = False
                return return_default
            else:
                self.devices = None
                return False
        else:
            return False

    def get_devices(self, device_type="hs100"):
        device_type = device_type.lower()
        if device_type is "hs100":
            return self.devices['hs100']
        elif device_type is "gpio":
            return self.devices['gpio_switches']
        else:
            return False

    @staticmethod
    def get_blackhouse_config(self):
        self.config_structure['blackhouse_configuration_directory'] = '/app/etc'
        self.config_structure['users_file'] = 'users.json'
        try:
            if os.environ['BLACKHOUSE_CONFIG_DIR']:
                self.config_structure['blackhouse_configuration_directory'] = os.environ['BLACKHOUSE_CONFIG_DIR']
        except KeyError:
            pass
        try:
            if os.environ['BLACKHOUSE_USERS_FILE']:
                self.config_structure['blackhouse_configuration_directory'] = os.environ['BLACKHOUSE_USERS_FILE']
        except KeyError:
            pass
        try:
            if os.environ['BLACKHOUSE_DEVICES']:
                self.config_structure['blackhouse_configuration_devices'] = os.environ['BLACKHOUSE_DEVICES']
        except KeyError:
            pass
        return self.config_structure


class GPIODeviceConfiguration:
    valid_gpio_pin = [4, 5, 6, 12, 13] + list(range(16, 26))

    def valid_pin(self, pin):
        return pin in self.valid_pin()

