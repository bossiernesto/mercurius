"""
.. module:: Mercury Proxy
   :platform: Linux
   :synopsis: HTTP/S and FTP local Proxy
   :copyright: (c) 2012-2013 by Ernesto Bossi.
   :license: BSD.

.. moduleauthor:: Ernesto Bossi <bossi.ernestog@gmail.com>

"""

from socketserver import ThreadingMixIn
from http.server import HTTPServer
from mercurius.config.AppContext import *
from .ProxyHandler import ProxyHandler
import socket
from mercurius.core.MercutyPacketsDao import MercuriusPacketsDao

# ThreadedHTTPServer
class MercuriusProxyServer(ThreadingMixIn, HTTPServer):
    """Threaded HTTPServer to thread many requests"""
    def init_dao(self):
        if not hasattr(self, 'packet_dao'):
            self.packet_dao = MercuriusPacketsDao()


def buildMercuryServer():
    hostname = socket.gethostname()
    port = appContext.getInstance().get(MERCURY, "port")
    mercuryInstance = MercuriusProxyServer((hostname, port), ProxyHandler)
    return mercuryInstance


def execMercury():
    import http.server

    http.server.test(ProxyHandler, MercuriusProxyServer)