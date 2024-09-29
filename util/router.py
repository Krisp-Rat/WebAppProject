from util.request import Request


class Router:

    def __init__(self):
        self.routes = []

    def add_route(self, method, path, action, exact_path=False):
        self.routes.append((method, path, action, exact_path))

    def route_request(self, request, handler):
        for route in self.routes:
            # exact path handling
            path = request.path == route[1] if route[3] else route[1] in request.path
            if route[0] == request.method and path:
                action = route[2]
                action(request, handler)
                return
        handler.request.sendall("HTTP/1.1 404".encode())


