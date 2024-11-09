from util.request import Request
class Parts:
    def __init__(self, headers, name, content, mime):
        self.headers = headers
        self.name = name
        self.content = content
        self.mimetype = mime


class MultipartRequest:
    def __init__(self, boundary, parts):
        self.boundary = boundary
        self.parts = parts

def parse_multipart(request):
    # check the content type
    content_length = int(request.headers.get('Content-Length'))
    content_type = request.headers.get('Content-Type')
    multipart, boundary = content_type.split('; ', 1)
    boundary = boundary.split("=", 1)[1]
    enc_boundary = ("\r\n--" + boundary).encode()
    end_boundary = enc_boundary + b"--"
    if content_length != len(request.body):
        print("---Content-Length error---")
        print("Got: ", len(request.body), "\nExpected: ", content_length)
    data = request.body.split(end_boundary, 1)[0]
    data = b"\r\n" + data
    data = data.split(enc_boundary + b"\r\n")[1:]
    parts = []
    if multipart != "multipart/form-data":
        return "", []
    for part in data:
        headers = {}
        # Separate headers from content
        header, content = part.split(b"\r\n\r\n", 1)
        # Split into key value pairs
        header = header.decode("utf-8").split("\r\n")
        for head in header:
            key, value = head.split(": ")
            headers[key] = value

        mime = headers.get("Content-Type", "text/plain")
        value = headers.get("Content-Disposition")
        name = value.split("; ")[1].split("=")[1].replace('"', "")

        part = Parts(headers, name, content, mime)
        parts.append(part)

    return MultipartRequest(boundary, parts)
