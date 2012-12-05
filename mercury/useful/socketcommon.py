import string
from  urlparse import urlparse

def host_url_port(url):
    url_tuple=urlparse(url)
    host_port = url_tuple[1]
    tokens = string.split(host_port, '@')
    if len(tokens) == 2:
        host_port = tokens[1]
    tokens = string.split(host_port, ':')
    if len(tokens) == 2:
        host = tokens[0]
        port = string.atoi(tokens[1])
    else:
        host = tokens[0]
        port = 80
    url = url_tuple[2]
    if not len(url):
        url = '/';
    if len(url_tuple[3]):
        url = url + ';' + url_tuple[3]
    if len(url_tuple[4]):
        url = url + '?' + url_tuple[4]

    return host, port, url