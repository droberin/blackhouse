import os


# Get configured switches
def get_switches():
    switches = {
        'ventilador': '192.168.1.13',
        'depuradora': '192.168.1.14',
        'oficina': '192.168.1.15',
        'arcade': '192.168.1.18',
    }
    return switches


def get_gpio_switches(device_type="pyzero"):
    if device_type == "pyzero":
        switches = [4, 5, 6, 12, 13] + list(range(16, 26))
    else:
        switches = [18]
    return switches


def get_blackhouse_config():
    config = {
        'blackhouse_configuration_directory': '/app/etc',
        'users_file': 'users.json',
    }
    try:
        if os.environ['BLACKHOUSE_CONFIG_DIR']:
            config['blackhouse_configuration_directory'] = os.environ['BLACKHOUSE_CONFIG_DIR']
    except KeyError:
        pass
    try:
        if os.environ['BLACKHOUSE_USERS_FILE']:
            config['blackhouse_configuration_directory'] = os.environ['BLACKHOUSE_USERS_FILE']
    except KeyError:
        pass
    return config


def get_remote_servers():
    servers = {
        "controlpi": "controlpi.local",
        "gate": {
            "proto": "http",
            "hostname": "pi2.local",
            "port": 5002,
            "username": "gate_admin",
            "password": "Hell'sGates",
        },
    }
    return servers
