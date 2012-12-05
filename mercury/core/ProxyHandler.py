from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import threading,urlparse
from SocketServer import ThreadingMixIn
from mercury.exceptions import  MercuryUnsupportedService

class ProxyHandler(BaseHTTPRequestHandler):

    __base =BaseHTTPRequestHandler
    __base_handle = __base.handle

    def __init__(self):
        self.supported_services=['http','ftp','https']
        super(ProxyHandler,self).__init__

    def supportedService(self,url):
        if(urlparse.urlparse(url).scheme not in self.supported_services):
            raise MercuryUnsupportedService()

    def do_GET(self):
        pass


    do_POST=do_GET
    do_UPDATE=do_GET
    do_DELETE=do_GET
    do_HEAD=do_GET



