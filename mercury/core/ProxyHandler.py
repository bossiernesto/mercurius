from BaseHTTPServer import BaseHTTPRequestHandler
import threading,urlparse
from mercury.exceptions import  MercuryUnsupportedService
import socket,select



class ProxyHandler(BaseHTTPRequestHandler):

    __base =BaseHTTPRequestHandler
    __base_handle = __base.handle

    def __init__(self):
        self.supported_services=['http','ftp','https']
        self.server_version="Mercury "+ __version__
        self.protocol_version="http" #TODO: extract this from appContext
        super(ProxyHandler,self).__init__

    def supportedService(self,scheme,fragment):
        if(scheme not in self.supported_services) or fragment:
            raise MercuryUnsupportedService()

    def do_connect(self):
        try:
            sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.setblocking(0)#TODO: Finish function
            self._con
        except:
            pass

    def do_GET(self):
        (scheme, netloc, path, params, query, fragment) = urlparse.urlparse(self.path)
        try:
            self.supported_services(scheme,fragment)
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.delegateActionByScheme(scheme)
        except MercuryUnsupportedService:
            self.send_error(400,"Bad URL: %s" % self.path)
        finally:
            soc.close()
            self.connection.close()

    do_POST=do_GET
    do_UPDATE=do_GET
    do_DELETE=do_GET
    do_HEAD=do_GET

    def _read_write(self, soc, max_idling=20, local=False):
        iw = [self.connection, soc]
    local_data = ""
    ow = []
    count = 0
    while 1:
        count += 1
        (ins, _, exs) = select.select(iw, ow, iw, 1)
        if exs: break
        if ins:
            for i in ins:
                if i is soc: out = self.connection
                else: out = soc
                data = i.recv(8192)
                if data:
                    if local: local_data += data
                    else: out.send(data)
                    count = 0
        if count == max_idling: break
    if local: return local_data
    return None