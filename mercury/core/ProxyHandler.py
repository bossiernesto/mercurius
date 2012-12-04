from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import threading,urlparse
from SocketServer import ThreadingMixIn
from mercury.exceptions import  MercuryUnsupportedService



class ProxyHandler(BaseHTTPRequestHandler):

    __base =BaseHTTPRequestHandler
    __base_handle = __base.handle

    def supportedService(self,url):
        if(urlparse.urlparse(url).scheme not in ['http','ftp','https']):
            raise MercuryUnsupportedService()




    def do_GET(self):
        pass

