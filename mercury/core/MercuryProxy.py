"""
.. module:: Mercury Proxy
   :platform: Linux
   :synopsis: HTTP/S and FTP local Proxy
   :copyright: (c) 2012-2013 by Ernesto Bossi.
   :license: MIT.

.. moduleauthor:: Ernesto Bossi <bossi.ernestog@gmail.com>

"""

from socketserver import ThreadingMixIn
from http.server import HTTPServer
from mercury.config.AppContext import *
from .ProxyHandler import ProxyHandler
import socket

#ThreadedHTTPServer
class MercuryProxyServer(ThreadingMixIn,HTTPServer):
    """Threaded HTTPServer to thread many requests"""
    pass

def buildMercuryServer():
    hostname=socket.gethostname()
    port=appContext.getInstance().get(MERCURY,"port")
    mercuryInstance=MercuryProxyServer((hostname,port),ProxyHandler)
    return mercuryInstance

def execMercury():
    import http.server
    http.server.test(ProxyHandler, MercuryProxyServer)