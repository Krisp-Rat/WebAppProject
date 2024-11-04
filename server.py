import socketserver
from util.request import Request
from util.router import Router
from util.hello_path import hello_path, home_path, support_path, chat_path, delete_path, \
    login, register, logout, upload
from util.multipart import parse_multipart

class MyTCPHandler(socketserver.BaseRequestHandler):

    def __init__(self, request, client_address, server):
        self.router = Router()
        self.router.add_route("GET", "/hello", hello_path, True)
        # TODO: Add your routes here
        self.router.add_route("GET", "/", home_path, True)
        self.router.add_route("GET", "/public/index.html", home_path, True)
        self.router.add_route("GET", "/public/", support_path)

        # message routing
        self.router.add_route("POST", "/chat-messages", chat_path, True)
        self.router.add_route("GET", "/chat-messages", chat_path, True)
        self.router.add_route("DELETE", "/chat-messages/", delete_path)

        # account routing
        self.router.add_route("POST", "/login", login, True)
        self.router.add_route("POST", "/register", register, True)
        self.router.add_route("POST", "/logout", logout, True)

        # upload routing
        self.router.add_route("POST", "/media-uploads", upload, True)
        super().__init__(request, client_address, server)

    def handle(self):
        rec = self.request.recv(2048)
        received_data = rec
        print("--- received data ---")
        print(received_data)
        print("--- end of data ---\n\n")
        request = Request(received_data)
        # test for headers only
        if len(received_data) == 0:
            print("No data received")
            return
        if (request.path == "/media-uploads" or request.path == "/register" or request.path == "/login" or request.path == "/logout") and len(request.body) == 0:
            print("Chrome Multipart")
            rec = self.request.recv(2048)
            received_data += rec
        while len(rec) == 2048:
            rec = self.request.recv(2048)
            received_data += rec
            if len(received_data) == 0:
                print("No data received")
                return
            print("--- received data ---")
            print(len(received_data))
            print(received_data)
            print("--- end of data ---\n\n")

        request = Request(received_data)

        self.router.route_request(request, self)


def main():
    host = "0.0.0.0"
    port = 8080
    socketserver.TCPServer.allow_reuse_address = True

    server = socketserver.TCPServer((host, port), MyTCPHandler)

    print("Listening on port " + str(port))
    server.serve_forever()


if __name__ == "__main__":
    main()
