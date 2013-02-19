"""
.. module:: Mercury Proxy Handler
   :platform: Linux
   :synopsis: HTTP/S and FTP local Proxy
   :copyright: (c) 2012-2013 by Ernesto Bossi.
   :license: MIT.

.. moduleauthor:: Ernesto Bossi <bossi.ernestog@gmail.com>

"""

from BaseHTTPServer import BaseHTTPRequestHandler
from mercury.exceptions import  MercuryUnsupportedService,MercuryConnectException
from MercuryHandlers import *
import socket,select,urlparse
from mercury.core import *

class ProxyHandler(BaseHTTPRequestHandler):

    __base =BaseHTTPRequestHandler
    __base_handle = __base.handle

    def __init__(self):
        self.server_version=appContext().getValue("Version")
        self.protocol_version=appContext().getValue("Protocol_Version")
        if common.pythonver_applies('3.0.0'):
            super().__init__()
        else:
            super(ProxyHandler,self).__init__()
        self.protocolDispatcher={"http":handleHTTP,"ftp":handleFTP,"https":handleHTTP}
        self.supported_services=[key for (key,value) in self.protocolDispatcher.iteritems()]
        self.logger=common.getLogger()

    def supportedService(self,scheme,fragment):
        if(scheme not in self.supported_services) or fragment:
            raise MercuryUnsupportedService()

    def _connect_to(self,netloc,sock):
        host_port = socketcommon.host_port(netloc)
        self.logger.info( "connect to %s:%d", host_port[0], host_port[1])
        try: sock.connect(host_port)
        except socket.error, arg:
            try: msg = arg[1]
            except: msg = arg
            self.send_error(404, msg)
            raise MercuryConnectException()

    def do_CONNECT(self):
        try:
            sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.setblocking(0)
            self._connect_to(self.path, sock)
            message=self.protocol_version +" 200 Connection established\r\n"
            self.log_request(message)
            self.wfile.write(message)
            if appContext.get(MERCURY,'verbose'):
                self.wfile.write("Proxy-agent: %s\r\n" % self.version_string())
            self.wfile.write("\r\n")
            self._read_write(sock, 300)
        except MercuryConnectException:
            self.logger.error("Unable to establish connection with host %s",self.path)
        finally:
            sock.close()
            self.connection.close()

    def do_GET(self):
        path = urlparse.urlparse(self.path) #(scheme, netloc, path, params, query, fragment)
        try:
            self.supportedService(path.scheme,path.fragment)
            sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.delegateActionByScheme(path.scheme,sock,self,path)
        except MercuryUnsupportedService:
            self.send_error(400,"Bad URL: %s" % self.path)
        except MercuryConnectException:
            self.logger.error("Unable to establish connection with host %s",self.path)
        finally:
            sock.close()
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
        local_data = ""
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
                    data=i.recv(8192)
                    if data:
                        if local: local_data += data
                        else: out.send(data)
                        count = 0
            if count == max_idling: break
        if local: return local_data
        return None

    def format_log(self,format,*args):
        return "%s - - [%s] %s\n" %(self.address_string(),self.log_date_time_string(),format%args)

    def log_error(self, format, *args):
        self.logger.error(self.format_log(format,args))

    def log_message(self, format, *args):
        self.logger.info(self.format_log(format,args))

    def log_request(self, code='-', size='-'):
        """Log an accepted request.
        This is called by send_response().
        """
        self.logger.info('"%s" %s %s',self.requestline, str(code), str(size))