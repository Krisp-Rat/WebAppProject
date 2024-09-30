class Router:

    def __init__(self):
        self.routes = []

    def add_route(self, method, path, action, exact_path=False):
        self.routes.append((method, path, action, exact_path))

    def route_request(self, request, handler):
        for route in self.routes:
            # exact path handling
            short_path = request.path[:len(route[1])]
            path = request.path == route[1] if route[3] else short_path == route[1]
            if route[0] == request.method and path:
                action = route[2]
                action(request, handler)
                return
        error = "content was not found".encode()
        length = len(error)
        response = f"HTTP/1.1 404 Not Found\r\nContent-Length: {length}\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
        response = response.encode() + error
        handler.request.sendall(response)


