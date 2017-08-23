import logging
import socket
from . import arcade

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class Switch:
    remote_ip = None
    remote_port = 9999
    state = None
    commands = {'info': '{"system":{"get_sysinfo":{}}}',
                'on': u'{"system":{"set_relay_state":{"state":1}}}',
                'off': '{"system":{"set_relay_state":{"state":0}}}',
                'cloudinfo': '{"cnCloud":{"get_info":{}}}',
                'wlanscan': '{"netif":{"get_scaninfo":{"refresh":0}}}',
                'time': '{"time":{"get_time":{}}}',
                'schedule': '{"schedule":{"get_rules":{}}}',
                'countdown': '{"count_down":{"get_rules":{}}}',
                'antitheft': '{"anti_theft":{"get_rules":{}}}',
                'reboot': '{"system":{"reboot":{"delay":1}}}',
                'reset': '{"system":{"reset":{"delay":1}}}'
                }

    def __init__(self, server, port=80):
        self.remote_ip = server
        self.remote_port = int(port)

    def activate(self):
        self.switch_requester(self.commands.get('on'))

    def deactivate(self):
        self.switch_requester(self.commands.get('off'))

    def info(self):
        self.switch_requester(self.commands.get('info'))

    def switch_requester(self, content=None):
        if content is None:
            print("Fail")
            return False
        else:
            try:
                sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock_tcp.connect((self.remote_ip, self.remote_port))
                print("Sending:     ", content)
#                sock_tcp.send(bytes(self.encrypt(content), 'utf8'))
                sock_tcp.send(self.encrypt(content).encode('utf8'))
                data = sock_tcp.recv(2048)
                sock_tcp.close()
                print("Sent:     ", content)
                print("Received: ", str(self.decrypt(data[4:])))
            except socket.error:
                return False
            return False

    def encrypt(self, string):
        key = 171
        result = "\0\0\0\0"
        for i in string:
            a = key ^ ord(i)
            key = a
            result += chr(a)
        return result

    def decrypt(self, string):
        key = 171
        result = ""
        string = string.decode('utf8')
        for i in string:
            i = str(i)
            a = key ^ ord(i)
            key = ord(i)
            result += chr(a)
        return result
