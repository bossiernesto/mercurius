from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer


class ThreadedHTTPServer(ThreadingMixIn,HTTPServer):
    """Threaded HTTPServer to thread many requests"""
    def __init__ (self, server_address, RequestHandlerClass, logger=None):
        HTTPServer.__init__ (self, server_address,RequestHandlerClass)

class MercuryProxyServer(ThreadedHTTPServer):
    pass