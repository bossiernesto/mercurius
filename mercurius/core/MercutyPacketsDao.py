__author__ = 'ernesto'


class MercuriusPacketsDao(object):
    def __init__(self):
        self.packets = dict()

    def add_packet(self, packet):
        self.packets[id(packet)] = packet