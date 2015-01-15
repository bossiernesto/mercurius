class HTTPHeader(object):
    pass


class HTTPParser(object):
    def parse_header(self, rfile):
        headers = {}
        name = ''
        while 1:
            line = input.readline()
            if line == '\r\n' or line == '\n':
                break
            if line[0] in ' \t':
                # continued header
                headers[name] = headers[name] + '\r\n ' + line.strip()
            else:
                i = line.find(':')
                assert(i != -1)
                name = line[:i].lower()
                if name in headers:
                    # merge value
                    headers[name] = headers[name] + ', ' + line.strip()
                else:
                    headers[name] = line[i+1:].strip()
        return headers