# This path is provided as an example of how to use the router
def hello_path(request, handler):
    response = "HTTP/1.1 200 OK\r\nContent-Length: 5\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nhello"
    handler.request.sendall(response.encode())


def home_path(request, handler):
    response = "HTTP/1.1 200 OK\r\nContent-Length: 0\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
    #Add code to read off content of file and set content length
    handler.request.sendall(response.encode())
