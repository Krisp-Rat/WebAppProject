import os

# This path is provided as an example of how to use the router
def hello_path(request, handler):
    response = "HTTP/1.1 200 OK\r\nContent-Length: 5\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nhello"
    handler.request.sendall(response.encode())


def home_path(request, handler):
    path = "public/index.html"
    if os.path.exists(path):
        visit = request.cookies.get("visits", "0")
        visit = int(visit) + 1

        with open(path, 'r') as home:
            page = home.read()
        page = page.replace("{{visits}}", str(visit), 1)
        page = page.encode()
        length = len(page)

        response = f"HTTP/1.1 200 OK\r\nContent-Length: {length}\r\nSet-Cookie: visits={visit}; Max-Age=3600\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
        response = response.encode() + page
        handler.request.sendall(response)
    else:
        handler.request.sendall("HTTP/1.1 404".encode())


def support_path(request, handler):
    path = request.path[1:]
    if os.path.exists(path):
        with open(path, 'rb') as image:
            img = image.read()
        mime = path.split(".")[-1]
        mime = mime if mime != "js" else "javascript"
        m_type = "text" if mime != "jpg" else "image"
        length = len(img)
        response = f"HTTP/1.1 200 OK\r\nContent-Length: {length}\r\nX-Content-Type-Options: nosniff\r\nContent-Type: {m_type}/{mime}; charset=utf-8\r\n\r\n"
        response = response.encode() + img
        handler.request.sendall(response)
    else:
        response = "HTTP/1.1 404".encode()

    handler.request.sendall(response)
