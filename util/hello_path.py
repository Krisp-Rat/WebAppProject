import os
import json
import uuid
import html
import bcrypt
import base64
from requests import post
from util.auth import extract_credentials, validate_password, percent_characters
from pymongo import MongoClient

docker_db = os.environ.get("DOCKER_DB", "false")
client = os.environ.get("CLIENT", "0ad0d9e4e00f48e8a05aa8e7829dd94c")
secret = os.environ.get("SECRET", "1f42a779f31c443697dcae9489d52cfe")

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
        # Get visit count or initialize to 0, then increment. Grab auth token or initialize
        visit = request.cookies.get("visits", "0")
        visit = int(visit) + 1
        auth = request.cookies.get("auth", str(uuid.uuid1().int))
        with open(path, 'r') as home:
            page = home.read()
        # Replace visit count and set the xsrf token
        page = page.replace("{{visits}}", str(visit), 1)
        truth, usr, uid, xsrf = authenticate(auth)
        page = page.replace("{{xsrf_token}}", xsrf)
        # Convert to bytes and set the content length
        page = page.encode()
        length = len(page)
        # Set Content Length, visit count, auth token, uuid. Send to the server.
        response = f"HTTP/1.1 200 OK\r\nContent-Length: {length}\r\nSet-Cookie: visits={visit}; Max-Age=3600\r\nSet-Cookie: auth={auth}; Max-Age=2592000; HttpOnly\r\nSet-Cookie: uid={uid}; Max-Age=2592000\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
        response = response.encode() + page
        handler.request.sendall(response)
    else:
        # If not found sent 404 error
        error = "content was not found".encode()
        length = len(error)
        response = f"HTTP/1.1 404 Not Found\r\nContent-Length: {length}\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
        response = response.encode() + error
        handler.request.sendall(response)


def support_path(request, handler):
    # Route all files in /public folder.
    path = request.path[1:]
    if os.path.exists(path):
        with open(path, 'rb') as image:
            img = image.read()
        # Determine mime type
        mime = path.split(".")[-1]
        mime = mime if mime != "js" else "javascript"
        mime = mime if mime != "ico" else "x-icon"
        m_type = "image" if mime == "jpg" or mime == "x-icon" else "text"

        # Set content length and mime type and send response
        length = len(img)
        response = f"HTTP/1.1 200 OK\r\nContent-Length: {length}\r\nX-Content-Type-Options: nosniff\r\nContent-Type: {m_type}/{mime}; charset=utf-8\r\n\r\n"
        response = response.encode() + img
        handler.request.sendall(response)
    else:
        # If not found send a 404 response
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
    if request.method == "POST":
        # Grab and decode message info from the request.
        body = request.body.decode('utf-8')
        body = json.loads(body)
        # Generate unique message ID, check for a message header
        mid = uuid.uuid1().int
        check = body.get("message", 0)
        if check != 0:
            # Grab content from message
            message = body["message"]
            xsrf_token = body["xsrf_token"]
            # escaping html for security
            message = html.escape(message)
            truth, usr, uid, xsrf = authenticate(auth_token, xsrf_token)
            if message != "" and xsrf:
                # Add username, uuid, message id, and message, to the MongoDB
                collection.insert_one({"username": f"{usr}", "message": f"{message}", "id": f"{mid}", "uid": f"{uid}"})
            else:
                # If the message isnt valid send a 403 response code
                handler.request.sendall(f"HTTP/1.1 403 submission was rejected".encode())
        # Send 202 response message
        response = f"HTTP/1.1 200 OK".encode()
    elif request.method == "GET":
        ret = []
        messages = collection.find()
        # Add each message to the return list with message content, username, uuid and message id
        for i in messages:
            message = i.get("message")
            username = i.get("username")
            uid = i.get("uid")
            m_id = i.get("id")
            ret.append({"message": message, "username": username, "id": f"{m_id}", "uid": f"{uid}"})
        # Convert list to JSON, and send response
        body = json.dumps(ret).encode()
        length = len(body)
        response = f"HTTP/1.1 200 OK\r\nContent-Length: {length}\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
        response = response.encode() + body
    handler.request.sendall(response)


def authenticate(token, xsrf=None):
    # Set default values for a guest
    usr = "Guest"
    uid = uuid.uuid1().int
    users = auth_tokens.find()
    token = token.encode()
    XS = str(uuid.uuid1())
    for user in users:
        # loop through authenticated users and check the hash of their passwd
        auth_token = user.get("token", "").encode()
        auth = bcrypt.checkpw(token, auth_token)
        if auth:
            # Grab uuid, username from the authenticated user
            uid = user.get("uid")
            usr = user.get("username")
            # If xsrf is set to None, return a new token
            if xsrf is None:
                print("was:", user.get("xsrf"), "is now:", XS)
                auth_tokens.update_one({"uid": uid}, {"$set": {"xsrf": XS}})
            # Evaluate the token
            else:
                XS = xsrf == user.get("xsrf")
            print("\nauthorized: ", usr)
            return auth, usr, uid, XS
    auth_hs = bcrypt.hashpw(token, bcrypt.gensalt()).decode('utf-8')

    auth_tokens.insert_one({"username": usr, "token": f"{auth_hs}", "uid": f"{uid}", "xsrf": f"{XS}"})
    print("---Guest not authorized---")
    return False, usr, uid, XS


def delete_path(request, handler):
    # Add confirmation here
    mid = request.path[15:]
    cookies = request.cookies
    auth_token = cookies.get("auth", "")
    auth, usr, uid, xsrf = authenticate(auth_token)
    set_resp = "403"
    if auth:
        msg = collection.find_one({"id": mid})
        if usr == msg.get("username"):
            print("user", msg.get("username"), "deletes:", msg.get("message"))
            collection.delete_one({"id": f"{mid}"})
            set_resp = "204"

    handler.request.sendall(f"HTTP/1.1 {set_resp}".encode())


def login(request, handler):
    usr, passwd = extract_credentials(request)
    match = False
    if validate_password(passwd):
        user = user_info.find_one({"username": usr})
        passwd_db = user.get("password", "").encode()
        passwd_bin = passwd.encode()
        match = bcrypt.checkpw(passwd_bin, passwd_db)
    set_token = ""
    if match:
        auth = str(uuid.uuid1().int)
        auth_hs = bcrypt.hashpw(auth.encode(), bcrypt.gensalt()).decode('utf-8')
        user = user_info.find_one({"username": usr})
        uid = user.get("uid")
        # Get rid of duplicates
        dupes = auth_tokens.find({"uid": uid})
        xsrf = uuid.uuid1()
        for d in dupes:
            auth_tokens.delete_one(d)
        auth_tokens.insert_one({"username": usr, "token": f"{auth_hs}", "uid": uid, "xsrf": f"{xsrf}"})
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
    auth = cookies.get("auth", "")
    auth, usr, uid, xsrf = authenticate(auth)
    set_resp = ""
    if auth and xsrf:
        auth_tokens.delete_one({"username": usr})
        set_resp = f"\r\nSet-Cookie: auth={auth}; Max-Age=3600"
    response = f"HTTP/1.1 302 Found\r\nLocation: /{set_resp}".encode()
    handler.request.sendall(response)


def send_token_request(request, handler):
    auth_string = client + ":" + secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = (base64.b64encode(auth_bytes)).decode("utf-8")
    url = "http://accounts.spotify.com/authorize"
    headers = {"Authorization": "Basic " + auth_base64, "Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "authorization_code", "redirect_uri": "http://localhost:8080/spotify"}
    result = post(url, headers=headers, data=data)
    length = len(result.content)
    response = f"HTTP/1.1 200 OK\r\nContent-Length: {length}\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
    response = response.encode() + result.content
    handler.request.sendall(response)

