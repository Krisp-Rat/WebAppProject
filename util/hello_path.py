import os
import json
import uuid
import html
from auth import extract_credentials, validate_password
from pymongo import MongoClient

docker_db = os.environ.get("DOCKER_DB", "false")

if docker_db == "true":
    print("Using docker database")
    mongo_client = MongoClient("mongo")
else:
    print("Using local database")
    mongo_client = MongoClient("localhost")
# This path is provided as an example of how to use the router

db = mongo_client["cse312"]
collection = db["chat"]


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
        id = request.cookies.get("uid", uuid.uuid1().int)

        response = f"HTTP/1.1 200 OK\r\nContent-Length: {length}\r\nSet-Cookie: visits={visit}; Max-Age=3600\r\nSet-Cookie: uid={id}; Max-Age=2592000\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
        response = response.encode() + page
        handler.request.sendall(response)
    else:
        error = "content was not found".encode()
        length = len(error)
        response = f"HTTP/1.1 404 Not Found\r\nContent-Length: {length}\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
        response = response.encode() + error
        handler.request.sendall(response)


def support_path(request, handler):
    path = request.path[1:]
    if os.path.exists(path):
        with open(path, 'rb') as image:
            img = image.read()
        mime = path.split(".")[-1]
        mime = mime if mime != "js" else "javascript"
        mime = mime if mime != "ico" else "x-icon"
        m_type = "image" if mime == "jpg" or mime == "x-icon" else "text"

        length = len(img)
        response = f"HTTP/1.1 200 OK\r\nContent-Length: {length}\r\nX-Content-Type-Options: nosniff\r\nContent-Type: {m_type}/{mime}; charset=utf-8\r\n\r\n"
        response = response.encode() + img
        handler.request.sendall(response)
    else:
        error = "content was not found".encode()
        length = len(error)
        response = f"HTTP/1.1 404 Not Found\r\nContent-Length: {length}\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
        response = response.encode() + error

    handler.request.sendall(response)


def chat_path(request, handler):
    response = f"HTTP/1.1 404 OK".encode()
    if request.method == "POST":
        body = request.body.decode('utf-8')
        body = json.loads(body)
        uid = request.cookies.get("uid", "")
        mid = uuid.uuid1().int
        check = body.get("message", 0)
        # Fix username
        if check != 0:
            message = body["message"]
            # escaping html for security
            message = html.escape(message)
            collection.insert_one({"username": "Guest", "message": f"{message}", "uid": f"{uid}", "id": f"{mid}"})
        response = f"HTTP/1.1 200 OK".encode()
    elif request.method == "GET":
        ret = []
        messages = collection.find()
        for i in messages:
            message = i.get("message", "")
            if message != "":
                username = i.get("username", "")
                uid = i.get("uid", "")
                id = i.get("id", "")
                ret.append({"message": message, "username": username, "id": f"{id}", "uid": f"{uid}"})

        body = json.dumps(ret).encode()
        length = len(body)
        response = f"HTTP/1.1 200 OK\r\nContent-Length: {length}\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
        response = response.encode() + body
    handler.request.sendall(response)


def delete_path(request, handler):
    mid = request.path[15:]

    print("Message ID", mid)
    collection.delete_one({"id": f"{mid}"})

    handler.request.sendall("HTTP/1.1 204".encode())


def login(request, handler):
    pass


def register(request, handler):
    usr, passwd = extract_credentials(request)
    valid = validate_password(passwd)

    # Register username and passwd
    if valid:
        salt = 0
        collection.insert_one({"username": usr, "password": f"{passwd}"})
        body = ""
    else:
        body = ""
        pass
    body = body.encode()
    length = len(body)
    response = f"HTTP/1.1 200 OK\r\nContent-Length: {length}\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
    response = response.encode() + body
    handler.request.sendall(response)


def logout(request, handler):
    pass
