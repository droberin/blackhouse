import logging
import os
import configobj


class BlackhouseConfiguration:
    config_structure = dict()
    devices = {
        "hs100": dict(),
        "gpio_switch": dict(),
        "gpio_push": dict(),
    }
    config_file = None

    def __init__(self):
        self.define_blackhouse_config()
        self.reload()

    def reload(self):

        devices_file = \
            self.config_structure['blackhouse_configuration_directory']\
            + '/'\
            + self.config_structure['blackhouse_configuration_devices']
        if devices_file and os.path.isfile(devices_file):
            raw_devices = configobj.ConfigObj(devices_file)
            return_default = True
            if len(raw_devices) > 0:
                for device in raw_devices:
                    try:
                        if raw_devices[device]['type'].lower() in self.devices:
                            device_type = raw_devices[device]['type'].lower()
                            self.devices[device_type][device] = raw_devices[device]
                        else:
                            logging.warning("Device type '{}' unknown for device '{}'".
                                            format(raw_devices[device]['type'], device)
                                            )
                    except KeyError:
                        logging.warning("Device {} can't be configured. Check config file.".format(device))
                        return_default = False
                return return_default
            else:
                self.devices = None
                return False
        else:
            return False

    def get_devices(self, device_type='hs100'):
        device_type = str(device_type).lower()
        if device_type in self.devices:
            return self.devices[device_type]
        else:
            return False

    def get_device_info(self, device_name, device_type='hs100'):
        if device_name in self.get_devices(device_type):
            return self.get_devices(device_type)[device_name]
        else:
            return False

    def define_blackhouse_config(self):
        self.config_structure['blackhouse_configuration_directory'] = os.environ.get('BH_CONF_DIR', '/app/etc')
        self.config_structure['users_file'] = os.environ.get('BH_USERS_FILE', 'users.json')
        self.config_structure['blackhouse_configuration_devices'] = os.environ.get('BH_DEVICES', 'devices.ini')
        return self.config_structure


class GPIODeviceConfiguration:
    valid_gpio_pin = [4, 5, 6, 12, 13] + list(range(16, 26))

    def valid_pin(self, pin):
        return pin in self.valid_gpio_pin

