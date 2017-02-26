"""
.. module:: Mercury Proxy Handler
   :platform: Linux
   :synopsis: HTTP/S and FTP local Proxy
   :copyright: (c) 2013-2015 by Ernesto Bossi.
   :license: BSD.

   special thanks to Suzuki, Hisao

.. moduleauthor:: Ernesto Bossi <bossi.ernestog@gmail.com>

"""

from mercurius.exceptions import MercuryUnsupportedService, MercuryConnectException, MercuriusRequestException
from .MercuriusHandlers import *
from socketserver import StreamRequestHandler
from mercurius.config.AppContext import *
from mercurius.core.http.HTTPS import HTTPS_Handshake_Flow
from mercurius.core.http import HTTPMessage
import select
import ssl
from http.client import HTTPConnection, HTTPSConnection, HTTPException
from urllib.parse import urlencode

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
            self.request = HTTPMessage.HTTPRequestBuilder().build(self.rfile, self.logger)
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

    # Verbs implementation

    def do_CONNECT(self, host, port, request):
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

        """
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
        # if appContext.getInstance().get(MERCURY, 'verbose'):
        # self.wfile.write(str.encode("Proxy-agent: %s\r\n" % self.version_string()))

    def make_request(self, connection, method, path, parameters, headers):
        try:
            return self._build_request(connection, method, path, parameters, headers)
        except IOError as e:
            self.logger.error('Failed building raw request to send. Reason: {0}'.format(e.__str__()))
            raise MercuriusRequestException(e.__str__())

    def _build_request(self, connection, method, path, parameters, headers):
        connection.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
        for header, v in headers.iteritems():
            # auto-fix content-length
            if header.lower() == 'content-length':
                connection.putheader(header, str(len(parameters)))
            else:
                connection.putheader(header, v)
        connection.endheaders()

        if len(parameters) > 0:
            connection.send(parameters)

    def _get_response(self, connection):
        raw_response = connection.getresponse()
        return HTTPMessage.HTTPResponseBuilder().build(raw_response, self.logger)

    def do_GET(self, host, port, request):
        from mercurius.core.http.HTTPMessage import GET_VERB

        try:
            connection = self._create_connection(host, port)
            self.make_request(connection, GET_VERB, request.get_path(), '', request.headers)
            response = self._get_response(connection)

            modified_response = self._delegate_response_protocol(response, request)
            self.add_response_to_dao(modified_response)
            data = modified_response.serialize()
            return data

        except MercuryConnectException as e:
            self.logger.error("Error Connecting to Host: {0}. Reason: {1}".format(self.host, e.__str__()))
        except MercuriusRequestException as e:
            self.logger.error(
                "Error Requesting to host {0}, on port {1}. Reason: {2}".format(self.host, self.port, e.__str__()))
        except HTTPException as e:
            self.logger.error(
                "Error on processing the response for host {0}. Reason {1}".format(self.host, e.__str__()))

    do_HEAD = do_GET
    do_UPDATE = do_GET
    do_DELETE = do_GET

    def do_POST(self, host, port, request):
        from mercurius.core.http.HTTPMessage import POST_VERB

        try:
            connection = self._create_connection(host, port)
            parameters = urlencode(request.get_params(POST_VERB))
            self.make_request(connection, POST_VERB, request.get_path(), parameters, request.headers)
            response = self._get_response(connection)

            modified_response = self._delegate_response_protocol(response, request)
            self.add_response_to_dao(modified_response)
            data = modified_response.serialize()
            return data

        except MercuryConnectException as e:
            self.logger.error("Error Connecting to Host: {0}. Reason: {1}".format(self.host, e.__str__()))
        except MercuriusRequestException as e:
            self.logger.error(
                "Error Requesting to host {0}, on port {1}. Reason: {2}".format(self.host, self.port, e.__str__()))
        except HTTPException as e:
            self.logger.error(
                "Error on processing the response for host {0}. Reason {1}".format(self.host, e.__str__()))

    def add_request_to_dao(self, request):
        self.server.packet_dao.add_request(request)

    def add_response_to_dao(self, response):
        self.server.packet_dao.add_response(response)

    def version_string(self):
        from mercurius.useful.common import bytedecode
        from mercurius.core.http.HTTPMessage import HTTP_VERSION

        return bytedecode(self.server_version) + ' ' + HTTP_VERSION
