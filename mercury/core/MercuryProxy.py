"""
.. module:: Mercury Proxy
   :platform: Linux
   :synopsis: HTTP/S and FTP local Proxy
   :copyright: (c) 2012-2013 by Ernesto Bossi.
   :license: MIT.

.. moduleauthor:: Ernesto Bossi <bossi.ernestog@gmail.com>

"""

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer
from mercury.config.AppContext import *
from ProxyHandler import ProxyHandler
import socket

#ThreadedHTTPServer
class MercuryProxyServer(ThreadingMixIn,HTTPServer):
    """Threaded HTTPServer to thread many requests"""
    def __init__ (self, server_address, RequestHandlerClass, logger=None):
        HTTPServer.__init__ (self, server_address,RequestHandlerClass)

def buildMercuryServer():
    hostname=socket.gethostname()
    port=appContext.getInstance.get(MERCURY,"port")
    mercuryInstance=MercuryProxyServer((hostname,port),ProxyHandler)
    return mercuryInstance

def execMercury(mercuryInstance):
    mercuryInstance.serve_forever()
