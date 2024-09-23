# This path is provided as an example of how to use the router
def hello_path(request, handler):
    response = "HTTP/1.1 200 OK\r\nContent-Length: 5\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nhello"
    handler.request.sendall(response.encode())


def home_path(request, handler):
    response = "HTTP/1.1 200 OK\r\nContent-Length: 5\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
    handler.request.sendall(response.encode())
