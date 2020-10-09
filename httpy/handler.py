from httpy import exceptions

class Handle:
    responses = {  # https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
        200: "OK",
        201: "Created",
        202: "Accepted",
        203: "Non-Authoritive Information",
        204: "No Content",
        205: "Reset Content",
        206: "Partial Content",
        207: "Multi-Status",
        208: "Already Reported",
        226: "IM Used",
        300: "Multiple Choices",
        301: "Moved Permanently",
        302: "Found",
        303: "See Other",
        304: "Not Modified",
        305: "Use Proxy",
        306: "Switch Proxy",
        307: "Temporary Redirect",
        308: "Permanent Redirect",
        400: "Bad Request",
        401: "Unauthorized",
        402: "Payment Required",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        406: "Not Acceptable",
        407: "Proxy Authentication Required",
        408: "Request Timeout",
        409: "Conflict",
        410: "Gone",
        411: "Length Required",
        412: "Precondition Failed",
        413: "Payload Too Large",
        414: "URI Too Long",
        415: "Unsupported Media Type",
        416: "Range Not Satisfiable",
        417: "Expectation Failed",
        418: "I'm a teapot",
        500: "Internal Server Error",
        501: "Not Implemented",
        502: "Bad Gateway"
    }

    def __init__(self, server, conn, addr, method="GET", path="/", request_protocal="HTTP/1.0", headers={}, body=None, thread=None):
        self.http = server
        self.socket = conn
        self.address = addr[0]
        self.port = addr[1]

        self.method = method
        self.path = path
        self.request_protocal = request_protocal

        self.headers = headers
        self.body = body

        self.thread = thread
        self._headers = {
            "X-Powered-By": "HTTPy v" + server._version
        }

        self.sent_response_code = False
        self.sent_headers = False
        self.sent_body = True
        self.request_finished = False

    def _end_request(self):
        if not self.sent_response_code:
            raise exceptions.InvalidHTTPSequence("Tried ending request before sending HTTP response code")

        if not self.sent_headers:
            raise exceptions.InvalidHTTPSequence("Tried ending request before flushing headers")

        if self.request_finished:
            raise exceptions.ResponseFinished("Response has already completed")

        if not self.sent_body:
            self.send_body_data("")

        self.http.end_interp_request(self.socket, (self.address, self.port), self.thread)
        self.request_finished = True

    def send_body_data(self, data):
        if not self.sent_headers:
            raise exceptions.InvalidHTTPSequence("Tried sending body data before flushing headers")

        if self.request_finished:
            raise exceptions.ResponseFinished("Response has already completed")

        if type(data) is not bytes:
            raise TypeError("Expected type bytes, got %s" % type(data))

        self.sent_body = True
        self.http.send_data_raw(self.socket, data, False)

    def flush_headers(self):
        if not self.sent_response_code:
            raise exceptions.InvalidHTTPSequence("Tried flushing headers before sending HTTP response code")

        if self.request_finished:
            raise exceptions.ResponseFinished("Response has already completed")

        if self.sent_headers:
            raise exceptions.AlreadySent("Already flushed headers")

        for header in self._headers:
            self.http.send_data(self.socket, "%s: %s" % (header, self._headers[header]))

        self.http.send_data(self.socket, "")
        self.sent_headers = True

    def send_response(self, code, message=None):
        if self.request_finished:
            raise exceptions.ResponseFinished("Response has already completed")

        if self.sent_response_code:
            raise exceptions.AlreadySent("Already sent response")

        self.sent_response_code = True
        self.http.send_data(self.socket, "HTTP/1.0 %s %s" % (code, message or self.responses[code]))

    def send_response_only(self, code, message=None):
        self.send_response(code, message)
        self.flush_headers()
        self.send_body_data("<h1>{} {}</h1><p>{}</p>".format(code, self.responses[code], message or self.responses[code]).encode())
        self._end_request()

    def handle(self):
        if hasattr(self, "on_"+self.method):
            func = getattr(self, "on_"+self.method)
            func()

            if not self.sent_response_code:
                self.send_response_only(502)
        else:
            self.send_response_only(501)
