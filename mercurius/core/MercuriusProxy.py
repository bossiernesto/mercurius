"""
.. module:: Mercury Proxy
   :platform: Linux
   :synopsis: HTTP/S and FTP local Proxy
   :copyright: (c) 2013-2014 by Ernesto Bossi.
   :license: BSD.

.. moduleauthor:: Ernesto Bossi <bossi.ernestog@gmail.com>

"""

from socketserver import ThreadingMixIn, TCPServer
from mercurius.config.AppContext import *
from .ProxyHandler import ProxyHandler
import socket
from mercurius.core.MercutyPacketsDao import MercuriusPacketsDao

# ThreadedHTTPServer


class MercuriusProxyServer(ThreadingMixIn, TCPServer):
    """Threaded HTTPServer to thread many requests"""
    allow_reuse_address = True

    def init_dao(self):
        if not hasattr(self, 'packet_dao'):
            self.packet_dao = MercuriusPacketsDao()


def buildMercuryServer():
    hostname = socket.gethostname()
    port = appContext.getInstance().get(MERCURY, "port")
    return MercuriusProxyServer((hostname, port), ProxyHandler)
