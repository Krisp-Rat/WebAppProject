import socketserver
from util.request import Request
from util.router import Router
from util.hello_path import hello_path, home_path, support_path, chat_path, delete_path, \
    login, register, logout, upload, web_socket
from util.websockets import parse_ws_frame, read_length


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

        # Web Socket routing
        self.router.add_route("GET", "/websocket", web_socket, True)
        super().__init__(request, client_address, server)

    def handle(self):
        received_data = self.request.recv(2048)
        request = Request(received_data)
        body_len = len(request.body)
        content_length = int(request.headers.get('Content-Length', str(body_len)))

        print("--- received data ---")
        print(received_data)
        print("--- end of data ---\n\n")

        # while body_len < content_length:
        #     additional_data = self.request.recv(2048)
        #     received_data += additional_data
        #     request = Request(received_data)
        #     body_len = len(request.body)
        #
        # request = Request(received_data)

        self.router.route_request(request, self)
        web_socket = True
        # while web_socket:
        #     received_data = self.request.recv(2048)
        #     print("--- received data ---")
        #     print(received_data)
        #     print("--- end of data ---\n\n")


def main():
    host = "0.0.0.0"
    port = 8080
    socketserver.TCPServer.allow_reuse_address = True

    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)

    print("Listening on port " + str(port))
    server.serve_forever()


if __name__ == "__main__":
    main()
