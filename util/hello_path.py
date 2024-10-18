import os
import json
import uuid
import html
import bcrypt
from util.auth import extract_credentials, validate_password
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
user_info = db["users"]
auth_tokens = db["auth_tokens"]


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
        # probably need to change uid here
        auth = request.cookies.get("auth", "")
        truth, usr, uid = authenticate(auth)
        response = f"HTTP/1.1 200 OK\r\nContent-Length: {length}\r\nSet-Cookie: visits={visit}; Max-Age=3600\r\nSet-Cookie: auth={auth}; Max-Age=2592000; HttpOnly\r\nSet-Cookie: uid={uid}; Max-Age=2592000\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
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
    # Get the usr and auth
    cookies = request.cookies
    auth_token = cookies.get("auth", "")
    truth, usr, uid = authenticate(auth_token)
    if request.method == "POST":
        body = request.body.decode('utf-8')
        body = json.loads(body)
        mid = uuid.uuid1().int
        check = body.get("message", 0)
        if check != 0:
            message = body["message"]
            # escaping html for security
            message = html.escape(message)
            if message != "":
                collection.insert_one({"username": f"{usr}", "message": f"{message}", "id": f"{mid}", "uid": f"{uid}"})
        response = f"HTTP/1.1 200 OK".encode()
    elif request.method == "GET":
        ret = []
        messages = collection.find()
        for i in messages:
            message = i.get("message")
            username = i.get("username")
            uid = i.get("uid")
            m_id = i.get("id")
            ret.append({"message": message, "username": username, "id": f"{m_id}", "uid": f"{uid}"})

        body = json.dumps(ret).encode()
        length = len(body)
        response = f"HTTP/1.1 200 OK\r\nContent-Length: {length}\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
        response = response.encode() + body
    handler.request.sendall(response)


def authenticate(token):
    usr = "Guest"
    uid = uuid.uuid1().int
    users = auth_tokens.find()
    token = token.encode()
    for user in users:
        auth_token = user.get("token", "").encode()
        auth = bcrypt.checkpw(token, auth_token)
        if auth:
            uid = user.get("uid")
            usr = user.get("username")
            print("\nauthorized: ", usr)
            return auth, usr, uid
    print("---Guest not authorized---")
    return False, usr, uid


def delete_path(request, handler):
    # Add confirmation here
    mid = request.path[15:]
    cookies = request.cookies
    auth_token = cookies.get("auth", "")
    auth, usr, uid = authenticate(auth_token)

    if auth:
        msg = collection.find_one({"id": mid})
        print("user", msg.get("username"), "deletes:", msg.get("message"))
        collection.delete_one({"id": f"{mid}"})
        set_resp = "204"
    else:
        set_resp = "403"
    handler.request.sendall(f"HTTP/1.1 {set_resp}".encode())


def login(request, handler):
    usr, passwd = extract_credentials(request)
    match = False
    if validate_password(passwd):
        user = user_info.find_one({"username": usr})
        #print("user", user.get("username", "nothing"))
        passwd_db = user.get("password", "").encode()
        passwd_bin = passwd.encode()
        match = bcrypt.checkpw(passwd_bin, passwd_db)
    set_token = ""
    if match:
        auth = str(uuid.uuid1().int)
        auth_hs = bcrypt.hashpw(auth.encode(), bcrypt.gensalt()).decode('utf-8')
        user = user_info.find_one({"username": usr})
        uid = user.get("uid")
        auth_tokens.insert_one({"username": usr, "token": f"{auth_hs}", "uid": uid})
        print("auth token", auth)
        set_token = f"\r\nSet-Cookie: auth={auth}; Max-Age=3600; HttpOnly"
        print("\n---Logged in successfully---\n")

    response = f"HTTP/1.1 302 Found\r\nLocation: /{set_token}".encode()
    handler.request.sendall(response)


def register(request, handler):
    usr, passwd = extract_credentials(request)
    dupe = user_info.find()
    duped = True
    for i in dupe:
        if i.get("username") == usr:
            print(f"-----Found duplicate username: {usr}-----")
            duped = False
    # Register username and passwd
    if validate_password(passwd) and duped:
        salt = bcrypt.gensalt()
        hash = bcrypt.hashpw(passwd.encode('utf-8'), salt).decode('utf-8')
        uid = uuid.uuid1().int
        user_info.insert_one({"username": usr, "password": f"{hash}", "uid": f"{uid}"})

    response = f"HTTP/1.1 302 Found\r\nLocation: /".encode()
    handler.request.sendall(response)


def logout(request, handler):
    cookies = request.cookies
    auth = cookies.get("auth")
    usr, uid = auth.split(auth)
    auth_tokens.delete_one({"username": usr})

    set_resp = f"\r\nSet-Cookie: auth={auth}; Max-Age=3600"
    response = f"HTTP/1.1 302 Found\r\nLocation: /{set_resp}".encode()
    handler.request.sendall(response)
