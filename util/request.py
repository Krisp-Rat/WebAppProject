class Request:

    def __init__(self, request: bytes):
        # TODO: parse the bytes of the request and populate the following instance variables
        request_split = request.split(b'\r\n')
        body_split = request.split(b'\r\n\r\n')
        R_line = request_split[0].split(b' ')
        self.body = body_split[-1]
        self.method = R_line[0].decode('utf-8')
        self.path = R_line[1].decode('utf-8')
        self.http_version = R_line[2].decode('utf-8')
        self.headers = {}
        request_split.pop(0)
        for i in request_split:
            if i.__contains__(b': '):
                i = i.split(b': ')
                key = i[0].decode('utf-8')
                val = i[1].decode('utf-8')
                self.headers[key] = val
            elif i.__contains__(b':'):
                i = i.split(b':')
                key = i[0].decode('utf-8')
                val = i[1].decode('utf-8')
                self.headers[key] = val

        self.cookies = {}


def test1():
    request = Request(b'GET / HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\nhello there')
    assert request.method == "GET"
    assert "Host" in request.headers
    assert request.headers["Host"] == "localhost:8080"  # note: The leading space in the header value must be removed
    assert request.body == b"hello there"  # There is no body for this request.
    # When parsing POST requests, the body must be in bytes, not str

    # This is the start of a simple way (ie. no external libraries) to test your code.
    # It's recommended that you complete this test and add others, including at least one
    # test using a POST request. Also, ensure that the types of all values are correct


if __name__ == '__main__':
    test1()
