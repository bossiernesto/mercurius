"""
.. module:: Mercury Proxy Handler
   :platform: Linux
   :synopsis: HTTP/S and FTP local Proxy
   :copyright: (c) 2012-2013 by Ernesto Bossi.
   :license: MIT.

   special thanks to Suzuki, Hisao

.. moduleauthor:: Ernesto Bossi <bossi.ernestog@gmail.com>

"""

from http.server import BaseHTTPRequestHandler
from mercurius.exceptions import  MercuryUnsupportedService,MercuryConnectException
from .MercuryHandlers import *
import socket,select,urllib.parse
from mercurius.core import *
from mercurius.config.AppContext import *

class ProxyHandler(BaseHTTPRequestHandler):

    __base =BaseHTTPRequestHandler
    __base_handle = __base.handle

    def __init__(self, request, client_address, server):
        self.server_version=appContext.getInstance().get(MERCURY,b'version')
        self.protocol_version="HTTP/1.1"
        self.protocolDispatcher={"http":handleHTTP,"ftp":handleFTP,"https":handleHTTP}
        self.supported_services=[key for (key,value) in self.protocolDispatcher.items()]
        self.logger=getMercuryLogger()
        super().__init__(request, client_address, server)

    def handle(self):
        (ip, port) =  self.client_address
        if hasattr(self, 'allowed_clients') and ip not in self.allowed_clients:
            self.raw_requestline = self.rfile.readline()
            if self.parse_request(): self.send_error(403)
        else:
            self.__base_handle()

    def supportedService(self,scheme,fragment):
        if(scheme not in self.supported_services) or fragment:
            raise MercuryUnsupportedService()

    def _connect_to(self,netloc,sock):
        host_port = socketcommon.host_port(netloc)
        self.logger.info( "connect to %s:%d", host_port[0], host_port[1])
        try: sock.connect(host_port)
        except socket.error as arg:
            try: msg = arg[1]
            except: msg = arg
            self.send_error(404, msg)
            raise MercuryConnectException()

    def do_CONNECT(self):
        try:
            sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self._connect_to(self.path, sock)
            message=self.protocol_version +" 200 Connection established\r\n"
            self.log_request(message)
            self.wfile.write(str.encode(message))
            if appContext.getInstance().get(MERCURY,'verbose'):
                self.wfile.write(str.encode("Proxy-agent: %s\r\n" % self.version_string()))
            self.wfile.write(str.encode("\r\n"))
            self._read_write(sock, 300)
        except MercuryConnectException:
            self.logger.error("Unable to establish connection with host %s",self.path)
        finally:
            sock.close()
            self.connection.close()

    def version_string(self):
        from mercurius.useful.common import bytedecode
        bytedecode(self.server_version) + ' ' + self.sys_version

    def do_GET(self):
        path = urllib.parse.urlparse(self.path) #(scheme, netloc, path, params, query, fragment)
        try:
            self.supportedService(path.scheme,path.fragment)
            self.sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.delegateActionByScheme(path.scheme,self.sock,self,path)
        except MercuryUnsupportedService:
            self.send_error(400,"Bad URL: %s" % self.path)
        except MercuryConnectException:
            self.logger.error("Unable to establish connection with host %s",self.path)
        finally:
            if hasattr(self,'sock'):
                self.sock.close()
            self.connection.close()

    do_POST=do_GET
    do_UPDATE=do_GET
    do_DELETE=do_GET
    do_HEAD=do_GET

    def delegateActionByScheme(self,scheme,socket,handler,path):
        dispatch=self.protocolDispatcher[scheme]   #get handler function according to scheme
        dispatch(socket,handler,path) #call it

    def _read_write(self, soc, max_idling=20, local=False):
        iw = [self.connection, soc]
        local_data = b''
        debug_data = b''
        ow = []
        count = 0
        while 1:
            count += 1
            (ins, _, exs) = select.select(iw, ow, iw, 1)
            if exs: break
            if ins:
                for i in ins:
                    if i is soc: out=self.connection
                    else: out=soc
                    data = i.recv(8192)
                    debug_data += data
                    if data:
                        if local: local_data += data
                        else: out.send(data)
                        count = 0
            if count == max_idling:
                #this is now a simple print, in the future it should be reifying this to an object, parse the http header to able to process it
                print(debug_data.decode('utf-8','ignore'))
                break
        if local:
            return local_data
        print(debug_data.decode('utf-8','ignore'))
        return None

    def format_log(self,format,*args):
        return "{0} - - [{1}] {2}\n".format(self.address_string(),self.log_date_time_string(),format % args[0])

    def log_error(self, format, *args):
        self.logger.error(self.format_log(format,args))

    def log_message(self, format, *args):
        self.logger.info(self.format_log(format,args))

    def log_request(self, code='-', size='-'):
        """Log an accepted request.
        This is called by send_response().
        """
        self.logger.info('"%s" %s %s',self.requestline, str(code), str(size))