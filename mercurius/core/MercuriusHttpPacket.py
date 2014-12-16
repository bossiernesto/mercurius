__author__ = 'ernesto'

import socket

try:
    from http_parser.parser import HttpParser
except ImportError:
    from http_parser.pyparser import HttpParser


class MercuriusHttpPacket(object):
    def __init__(self, raw_data, path):
        self.raw_data = raw_data
        self.path = path
        self.ip = self.get_ip(path)

        self.headers = self.set_headers(raw_data)

    def set_headers(self, raw_data):
        parser = HttpParser()

        recved = len(raw_data)
        parser.execute(raw_data, recved)
        return parser.get_headers()

    def get_ip(self, path):
        from urllib.parse import ParseResult

        actual_path = path.netloc if isinstance(path, ParseResult) else path.split(':')[0]
        return socket.gethostbyname(actual_path)

    def __repr__(self):
        print("{0} {1}".format(self.headers ,self.ip))
