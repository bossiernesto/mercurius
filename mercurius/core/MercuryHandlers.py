"""
.. module:: Mercury Handlers
   :platform: Linux
   :synopsis: HTTP/S and FTP local Proxy
   :copyright: (c) 2012-2013 by Ernesto Bossi.
   :license: MIT.

.. moduleauthor:: Ernesto Bossi <bossi.ernestog@gmail.com>

"""
from urllib.parse import urlunparse
from mercurius.config.AppContext import getMercuryLogger
import ftplib

def handleHTTP(socket,handler,path):
    # path -> (scheme, netloc, path, params, query, fragment)
    handler._connect_to(path.netloc,socket)
    handler.log_request()

    content = "%s %s %s\r\n" % (handler.command,
                               urlunparse(('', '', path.path, path.params, path.query, '')),
                               handler.request_version)
    socket.send(str.encode(content))
    handler.headers['Connection'] = 'close'
    del handler.headers['Proxy-Connection'] #TODO: use a decorator to be able to modify the package status
                                            #TODO: Add hook to delegate enabled plug-ins
    for key_val in handler.headers.items():
        socket.send(str.encode("%s: %s\r\n" % key_val))
    socket.send(str.encode("\r\n"))
    handler._read_write(socket)


def handleFTP(socket,handler,path):
    # path -> (scheme, netloc, path, params, query, fragment)
    # fish out user and password information
    i = path.netloc.find ('@')
    if i >= 0:
        login_info, netloc = path.netloc[:i], path.netloc[i+1:]
        try:
            user, passwd = login_info.split (':', 1)
        except ValueError:
            user, passwd = "anonymous", None
        else: user, passwd ="anonymous", None
        handler.log_request ()
        try:
            ftp = ftplib.FTP (netloc)
            ftp.login (user, passwd)
            if handler.command == "GET":
                ftp.retrbinary ("RETR %s"%path, handler.connection.send)
            ftp.quit ()
        except Exception as e:
            getMercuryLogger().log_warning("FTP Exception: %s",e)