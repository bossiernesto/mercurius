class HTTPS_Handshake_Flow(object):
    def send_ack_package(self, socket):
        from mercurius.core.http.HTTPMessage import HTTP_OK, HTTPResponse, HTTP_VERSION
        # Send a 200 response to acknowledge the connection
        ack = HTTPResponse(HTTP_VERSION, HTTP_OK, "Connection Established")
        socket.send(ack.serialize())
