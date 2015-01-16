# code based on http://www.w3.org/2000/10/swap/test/reason/,pfproxy.py

from mercurius.core.http.HTTPParser import HTTPParser
from mercurius.exceptions import MercuriusHTTPException, MercuriusHeaderException
from mercurius.config.AppContext import getMercuryLogger
import copy
import urllib.parse as urlibparse

MESSAGE_EOL = "\r\n"
HTTP_OK = 200
HTTP_VERSION = "HTTP/1.1"

# verbs constants
CONNECT_VERB = "CONNECT"
HEAD_VERB = "HEAD"
GET_VERB = "GET"
POST_VERB = "POST"
PUT_VERB = "PUT"
DELETE_VERB = "DELETE"
TRACE_VERB = "TRACE"
OPTIONS_VERB = "OPTIONS"


class HTTPMessageBuilder(object):
    def _read_body(self, rfile):
        chunked = False
        bodylen = self.headers.get('content-length', 0)

        if self.headers.get('transfer-encoding') == "chunked":
            chunked = True

        # Read HTTP body (if present)
        body = ""
        if bodylen > 0:
            body = rfile.read(bodylen)

        elif chunked:
            # Chunked encoding
            while True:
                # Determine chunk length
                chunklen = rfile.readline()
                chunklen = int(chunklen, 16)

                if chunklen == 0:
                    break

                # Read the whole chunk
                chunk = ""
                chunk = rfile.read(chunklen)
                body += chunk

                # Read trailing CRLF
                eol = rfile.read(2)
                self._check_chunked_eol(eol)

        return body

    def _check_chunked_eol(self, eol):
        if eol != MESSAGE_EOL:
            self.logger.error('Could not read chunked HTTP body.')
            raise MercuriusHTTPException('Could not read chunked HTTP body')

    def _fix_url_https(self, scheme, url, headers):
        if (url.find('http') != 0) and (url[0] == '/'):
            if 'host' in headers:
                url = scheme + '://' + headers['Host'][0] + url
        return url

    def build(self, rfile, logger):
        self.logger = logger
        self.request = rfile.readline().rstrip(MESSAGE_EOL)
        self.kramer = False

        if self.request == '':
            self.kramer = True

        method, url, protocol = self.request.split()

        self.headers = HTTPParser().parse_header(rfile)
        body = self._read_body(rfile)
        return self.build_package(method, url, protocol, self.headers, body)

    def build_package(self, method, url, protocol, headers, body):
        raise NotImplemented


class HTTPRequestBuilder(HTTPMessageBuilder):
    def build_package(self, method, url, protocol, headers, body):
        url_request = self._fix_url_https('https', url, headers)
        if self.kramer:
            return None
        return HTTPRequest(method, url_request, protocol, headers, body)


class HTTPResponseBuilder(HTTPMessageBuilder):
    # using response from http.client
    def build(self, raw_response, logger):
        self.logger = logger
        self.kramer = False

        body = raw_response.read()
        protocol = "HTTP/1.0" if raw_response.version == 10 else "HTTP/1.1"

        code = raw_response.status
        message = raw_response.reason

        return self.build_package(code, message, protocol, raw_response.msg.headers, body)

    def build_package(self, code, message, protocol, headers, body):
        response = HTTPResponse(code, message, protocol, headers, body)
        if self.kramer:
            response.mark_as_kramer()
        return response


class HTTPMessage(object):
    uid = 0

    @classmethod
    def increment_uid(cls):
        cls.uid += 1

    def __init__(self, protocol, headers, body):
        self.kramer = False
        self.logger = getMercuryLogger()
        self.protocol = protocol
        self.headers = headers
        self.body = body
        self.uid = HTTPMessage.uid
        self.__class__.increment_uid()

    def set_header(self, header_name, value):
        self.headers[header_name] = value

    def add_header(self, header_name, value, overwrite=False):
        if header_name in self.headers and not overwrite:
            self.logger.debug(
                'Tried to overwrite the existing header_name: {0} with value:{1}'.format(header_name, value))
            raise MercuriusHeaderException(
                "Tried to overwrite an existent header value, set overwrite=True to skip this error")
        self.headers[header_name] = value

    def remove_header(self, header_name):
        try:
            del self.headers[header_name]
        except KeyError:
            self.logger.debug('Tried to remove an inexistent header')

    def mark_as_kramer(self):
        self.kramer = True

    def is_chunked(self):
        return self.headers.get('transfer-encoding') == "chunked"

    def clone_message(self):
        return copy.deepcopy(self)

    def is_keepalive(self):
        connection_header = self.headers.get('connection', None)
        proxy_connection_header = self.headers.get('proxy-connection', None)
        return connection_header == 'keep-alive' or proxy_connection_header == 'keep-alive'

    def _fix_inconsistencies(self):
        self._fix_content_lenght()

    def _fix_content_lenght(self):
        content_lenght = self.headers.get('content-length', 0)
        body_len = len(self.body)
        if (content_lenght != body_len):
            self.add_header('content-length', body_len, True)

    def set_peer(self):
        pass

    def serialize(self):
        serialized = "{0}{1}{2}{3}{4}".format(self.serialize_prelude(), MESSAGE_EOL, self._serialize_headers(),
                                              MESSAGE_EOL, self._serialize_body())
        return bytes(serialized, 'UTF-8')

    def serialize_prelude(self):
        raise NotImplemented

    def _serialize_headers(self):
        data = []
        for name, value in self.headers.items():
            data.append("{0}: {1}\r\n".format(name, value))
        return ''.join(data)

    def _serialize_body(self):
        if not self.is_chunked():
            return self.body
        return "{0}{1}{2}{3}{4}{5}{6}{7}".format(len(self.body), MESSAGE_EOL, self.body, MESSAGE_EOL, MESSAGE_EOL, "0",
                                                 MESSAGE_EOL, MESSAGE_EOL)


class HTTPRequest(HTTPMessage):
    def __init__(self, method, url, protocol, headers, body):
        self.method = method.upper()
        self.url = url
        super().__init__(protocol, headers, body)
        self._parse_host_port()

    def is_connect(self):
        return self.method == 'CONNECT'

    def is_get_like_request(self):
        return self.method in [GET_VERB, HEAD_VERB]

    def is_post_like_request(self):
        return self.method in [POST_VERB]

    def set_params(self):
        self.params = {}
        if self.is_get_like_request():
            params = urlibparse.urlparse(self.url).query
            if len(params) > 0:
                self.params.update(urlibparse.parse_qs(params))
            return
        if self.is_post_like_request() and len(self.body) > 0:
            self.params.update(urlibparse.parse_qs(self.body, keep_blank_values=True))

    def get_params(self):
        if not hasattr(self, 'params'):
            self.set_params()
        return self.params

    def get_path(self):
        parsed = urlibparse.urlparse(self.url)
        path = parsed.path
        if len(parsed.params) > 0:
            path += ";{0}".format(parsed.params)
        if len(parsed.query) > 0:
            path += "?{0}".format(parsed.query)
        if len(parsed.fragment) > 0:
            path += "#{0}".format(parsed.fragment)
        return path

    def clone_request(self):
        return self.clone_message()

    def _parse_connect_host_port(self):
        temp = self.url.split(":")
        self.host = temp[0]
        self.port = int(temp[1]) if len(temp) > 0 else 80

    def _parse_normal_host_port(self):
        parsed = urlibparse.urlparse(self.url)  # (scheme, netloc, path, params, query, fragment)
        self.host = parsed.hostname
        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme == "https" else 80
        self.port = port
        self.scheme = parsed.scheme
        self.fragment = parsed.fragment

    def _parse_host_port(self):
        if self.method == CONNECT_VERB:
            self._parse_connect_host_port()
            return
        self._parse_normal_host_port()

    def get_host_port(self):
        return self.host, self.port

    def get_method(self):
        return self.method.upper()

    def get_scheme_fragment(self):
        return self.scheme, self.fragment

    def serialize_prelude(self):
        return "{0} {1} {2}".format(self.method, self.url, self.protocol)


class HTTPResponse(HTTPMessage):
    def __init__(self, code, message, protocol, headers=None, body=""):
        self.code = code
        self.message = message
        super().__init__(protocol, headers, body)

    def clone_response(self):
        return self.clone_message()

    def serialize_prelude(self):
        return "{0} {1} {2}".format(self.protocol, self.code, self.message)

    def add_request_associated(self, request):
        import weakref

        request_weakref = weakref.ref(request)
        self.request = request_weakref

    def get_request_associated(self):
        if hasattr(self, 'request'):
            return self.request()
        raise AttributeError
