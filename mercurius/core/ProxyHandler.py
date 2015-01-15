"""
.. module:: Mercury Proxy Handler
   :platform: Linux
   :synopsis: HTTP/S and FTP local Proxy
   :copyright: (c) 2012-2013 by Ernesto Bossi.
   :license: BSD.

   special thanks to Suzuki, Hisao

.. moduleauthor:: Ernesto Bossi <bossi.ernestog@gmail.com>

"""

from mercurius.exceptions import MercuryUnsupportedService, MercuryConnectException
from .MercuriusHandlers import *
from socketserver import StreamRequestHandler
from mercurius.config.AppContext import *
from mercurius.core.http.HTTPS import HTTPS_Handshake_Flow
from mercurius.core.http import HTTPMessage
import select
import ssl
from http.client import HTTPConnection, HTTPSConnection, HTTPException

DEFAULT_CERT_FILE = './certs/cert.pem'


class ProxyHandler(StreamRequestHandler):
    __base = StreamRequestHandler
    __base_handle = __base.handle

    def __init__(self, request, client_address, server):
        self.server_version = appContext.getInstance().get(MERCURY, b'version')

        self.protocol_request_dispatcher = {"http": handleHTTPRequest, "https": handleHTTPSRequest}
        self.protocol_response_dispatcher = {"http": handleHTTPResponse, "https": handleHTTPSResponse}
        self.supported_services = [key for (key, value) in self.protocol_request_dispatcher.items()]

        self.logger = getMercuryLogger()
        self.keep_alive = False
        self.packets_served = 0
        self.server.init_dao()  # DAO lazy initizalization

        self._previous_host = None
        self._previous_port = None
        self.peer = False
        self.keep_alive_conn = None
        super().__init__(request, client_address, server)

    def _wait_read(self, socket):
        select.select([socket], [], [])

    def previous_connection(self, host):
        return self.keep_alive_conn and self._previous_host == host

    def _create_connection(self, host, port):

        if self.previous_connection(host):
            return self.keep_alive_conn

        try:
            connection = HTTPSConnection(host, port) if self.peer else HTTPConnection(host, port)

            if self.keep_alive:
                self.keep_alive_conn = connection
            self._previous_host = host
            self._previous_port = port

        except HTTPException as e:
            self.logger.error("Could not connect with host: {0} on port {1}".format(host, port))
            raise MercuryConnectException(e.__str__())

        return connection

    def _create_https_connection(self):
        """
        https full handshake

        Client                                  Server

        ClientHello              -------->
                                                ServerHello
                                                Certificate*
                                                ServerKeyExchange*
                                                CertificateRequest*
                                 <--------      ServerHelloDone
        Certificate*
        ClientKeyExchange
        CertificateVerify*
        [ChangeCipherSpec]
        Finished                  -------->
                                               [ChangeCipherSpec]
                                  <--------             Finished
        Application Data          <------->     Application Data

        :return:
        """
        pass

    def send_response(self, response):
        self.wfile.write(response)

    def _close_target(self):
        if self.target:
            self.target.close()
            self.target = None

    def finish(self):
        if not self.keep_alive:
            self._close_target()
            super().finish()
        self.handle()

    def increment_packet_served(self):
        if self.packets_served > 0:
            self.logger.debug("Proxy Handler already used to serve {0} packets.".format(self.packets_served))
        self.packets_served += 1

    def handle(self):
        if self.keep_alive:
            self._wait_read(self.request)
            self.increment_packet_served()

        try:
            self.request = HTTPMessage.HTTPRequestBuilder.build(self.rfile, self.logger)
            if self.request is None:
                return None
        except Exception as e:
            self.logger.error('Error creating request ' + e.__str__())

        self.keep_alive = self.request.is_keepalive()
        self.host, self.port = self.request.get_host_port()
        method = self.request.get_method()

        modified_request = self._delegate_request_protocol(self.request)
        self.request = modified_request

        method_callback = getattr(self, 'do_{0}'.format(method))
        response = method_callback(self.host, self.port, self.request)

    def supported_service(self, scheme, fragment):
        if (scheme not in self.supported_services) or fragment:
            raise MercuryUnsupportedService()

    def _get_dispatcher_delegator(self, request, dispatcher_name):
        scheme, fragment = request.get_scheme_fragment()
        self.supported_service(scheme, fragment)

        dispatcher = getattr(self, dispatcher_name)
        dispatch = dispatcher[scheme]

        return dispatch

    def _delegate_request_protocol(self, request):
        dispatch = self._get_dispatcher_delegator(request, 'protocol_request_dispatcher')

        return dispatch(request, self.host, self.port)

    def _delegate_response_protocol(self, response, request):
        dispatch = self._get_dispatcher_delegator(request, 'protocol_response_dispatcher')

        return dispatch(response, request)

    # def _connect_to(self, netloc, sock):
    # host_port = socketcommon.host_port(netloc)
    # self.logger.info("connect to %s:%d", host_port[0], host_port[1])
    #     try:
    #         sock.connect(host_port)
    #     except socket.error as arg:
    #         try:
    #             msg = arg[1]
    #         except:
    #             msg = arg
    #         self.send_error(404, msg)
    #         raise MercuryConnectException()

    # Verbs implementation

    def do_CONNECT(self, host, port, request):

        socket_req = self.request
        certfilename = DEFAULT_CERT_FILE
        socket_ssl = ssl.wrap_socket(socket_req, server_side=True, certfile=certfilename,
                                     ssl_version=ssl.PROTOCOL_SSLv23, do_handshake_on_connect=False)

        HTTPS_Handshake_Flow().send_ack_package(socket_req)

        host, port = socket_req.getpeername()
        self.logger.debug("Send ack to the peer %s on port %d for establishing SSL tunnel" % (host, port))

        while True:
            try:
                socket_ssl.do_handshake()
                break
            except (ssl.SSLError, IOError) as e:
                self.logger.error("Error on SSL Handshake. Reason: {0}".format(e.__str__()))
                return

        # Switch to new socket
        self.peer = True
        self.request = socket_ssl

        self.setup()
        self.handle()
        #     if appContext.getInstance().get(MERCURY, 'verbose'):
        #         self.wfile.write(str.encode("Proxy-agent: %s\r\n" % self.version_string()))


    def make_request(self, connection, method, parameters, headers):
        pass

    def do_GET(self, host, port, request):
        from mercurius.core.http.HTTPMessage import GET_VERB

        try:
            connection = self._create_connection(host, port)
            self.make_request(connection, GET_VERB, '', request.headers)
            response = self._get_response(connection)

            response_modified = self._delegate_response_protocol(response, request)
            data = response_modified.serialize()
            return data

        except (MercuryConnectException, Exception) as e:
            pass  #pass for now...


    do_HEAD = do_GET
    do_UPDATE = do_GET
    do_DELETE = do_GET

    def do_POST(self, host, port, request):
        from mercurius.core.http.HTTPMessage import POST_VERB

        connection = self._create_connection(host, port)
        ## TODO: Continue


    def delegateActionByScheme(self, scheme, socket, handler, path):
        dispatch = self.protocolDispatcher[scheme]  # get handler function according to scheme
        dispatch(socket, handler, path)  # call it

    # def _read_write(self, soc, max_idling=20, local=False, path=None):
    #     iw = [self.connection, soc]
    #     local_data = b''
    #     debug_data = b''
    #     ow = []
    #     count = 0
    #     while 1:
    #         count += 1
    #         (ins, _, exs) = select.select(iw, ow, iw, 1)
    #         if exs: break
    #         if ins:
    #             for i in ins:
    #                 if i is soc:
    #                     out = self.connection
    #                 else:
    #                     out = soc
    #                 data = i.recv(8192)
    #                 debug_data += data
    #                 if data:
    #                     if local:
    #                         local_data += data
    #                     else:
    #                         out.send(data)
    #                     count = 0
    #         if count == max_idling:
    #             # this is now a simple print, in the future it should be reifying this to an object, parse the http header to able to process it
    #             #print(debug_data.decode('utf-8', 'ignore'))
    #             self.reify_raw_data(debug_data, path)
    #             break
    #     if local:
    #         return local_data
    #     #print(debug_data.decode('utf-8', 'ignore'))
    #     self.reify_raw_data(debug_data, path)
    #     return None


    def add_request_to_dao(self, request):
        self.server.packet_dao.add_request(request)

    def add_response_to_dao(self, response):
        self.server.packet_dao.add_response(response)

    def version_string(self):
        from mercurius.useful.common import bytedecode

        return bytedecode(self.server_version) + ' ' + self.sys_version

    def format_log(self, format, *args):
        return "{0} - - [{1}] {2}\n".format(self.address_string(), self.log_date_time_string(), format % args[0])

    def log_error(self, format, *args):
        self.logger.error(self.format_log(format, args))

    def log_message(self, format, *args):
        self.logger.info(self.format_log(format, args))

    def log_request(self, code='-', size='-'):
        """Log an accepted request.
        This is called by send_response().
        """
        self.logger.info('"%s" %s %s', self.requestline, str(code), str(size))