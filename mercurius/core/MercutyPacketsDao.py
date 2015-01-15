
class MercuriusPacketsDao(object):
    def __init__(self):
        self.requests = dict()
        self.responses = dict()

    def add_request(self, packet):
        self.requests[id(packet)] = packet

    def add_response(self, response):
        self.responses[id(response)] = response