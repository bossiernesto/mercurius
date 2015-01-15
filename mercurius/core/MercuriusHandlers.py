"""
.. module:: Mercury Handlers
   :platform: Linux
   :synopsis: HTTP/S and FTP local Proxy
   :copyright: (c) 2012-2013 by Ernesto Bossi.
   :license: BSD.

.. moduleauthor:: Ernesto Bossi <bossi.ernestog@gmail.com>

"""
from urllib.parse import urlunparse
from mercurius.config.AppContext import getMercuryLogger
import ftplib
from mercurius.useful.common import encode_str


def handleHTTP(socket, handler, path):
    # path -> (scheme, netloc, path, params, query, fragment)
    handler._connect_to(path.netloc, socket)
    handler.log_request()

    content = "%s %s %s\r\n" % (handler.command,
                                urlunparse(('', '', path.path, path.params, path.query, '')),
                                handler.request_version)
    socket.send(encode_str(content))
    handler.headers['Connection'] = 'close'

    del handler.headers['Proxy-Connection']  # TODO: use a decorator to be able to modify the package status
    # TODO: Add hook to delegate enabled plug-ins
    print(handler.headers)
    for key_val in handler.headers.items():
        socket.send(encode_str("%s: %s\r\n" % key_val))
    socket.send(encode_str("\r\n"))
    handler._read_write(socket, path=path)


def handleFTP(socket, handler, path):
    # path -> (scheme, netloc, path, params, query, fragment)
    # fish out user and password information
    i = path.netloc.find('@')
    if i >= 0:
        login_info, netloc = path.netloc[:i], path.netloc[i + 1:]
        try:
            user, passwd = login_info.split(':', 1)
        except ValueError:
            user, passwd = "anonymous", None
        else:
            user, passwd = "anonymous", None
        handler.log_request()
        try:
            ftp = ftplib.FTP(netloc)
            ftp.login(user, passwd)
            if handler.command == "GET":
                ftp.retrbinary("RETR %s" % path, handler.connection.send)
            ftp.quit()
        except Exception as e:
            getMercuryLogger().log_warning("FTP Exception: %s", e)

def GenericHandler(object):

    def __init__(self):
        pass

    def handle_object(self, object_to_modify):
        raise NotImplemented

def handleHTTPRequest():
    pass

def handleHTTPSRequest():
    pass

def handleHTTPResponse():
    pass

def handleHTTPSResponse():
    pass
