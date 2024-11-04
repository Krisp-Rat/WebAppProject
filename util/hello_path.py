import os
import json
import uuid
import html
import bcrypt
import ffmpeg
from PIL import Image, ImageSequence
from util.auth import extract_credentials, validate_password
from util.multipart import parse_multipart
from pymongo import MongoClient
import io

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
uploads = db["uploads"]


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
    if "/public/image/" in request.path:
        path = "public/image/" + request.path[len("/public/image/"):].replace("/", "_")
    else:
        path = request.path[1:]
    path = get_file(path)
    if os.path.exists(path):
        with open(path, 'rb') as image:
            img = image.read()
        # Determine mime type
        mime = path.split(".")[-1]
        mime = mime if mime != "js" else "javascript"
        mime = mime if mime != "ico" else "x-icon"
        m_type = "image" if mime == "jpg" or mime == "x-icon" else "text"
        m_type = "video" if mime == "mp4" else m_type
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


signatures = {"image/jpeg": [b"\xff\xd8\xff\xe0", b"\xff\xd8\xff\xdB", b"\xff\xd8\xff\xee"],
              "image/png": [b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"],
              "image/gif": [b"\x47\x49\x46\x38\x37\x61", b"\x47\x49\x46\x38\x39\x61"],
              "video/mp4": [b"\x66\x74\x79\x70\x69\x73\x6f\x6d", b"\x66\x74\x79\x70\x4d\x53\x4e\x56"]}


def mime_sniffer(content):
    for type, signature in signatures.items():
        for sig in signature:
            cont = content[:len(sig)]
            mp_cont = content[4:len(sig) + 4]
            if cont == sig:
                return type
            elif mp_cont == sig:
                return type

    return "text/plain"


def upload(request, handler):
    multipart = parse_multipart(request)
    token = request.cookies.get("auth", "")
    auth, usr, uid, xsrf = authenticate(token)
    parts = multipart.parts
    for part in parts:
        mime = mime_sniffer(part.content)
        # this line strips the provided file name of spaces and /
        provided_filename = part.headers.get("Content-Disposition").split("; ")[2].split("=")[1].replace('"',
                                                                                                         "").replace(
            "/", "-").replace(" ", "_")
        extension = mime.split("/")[-1].replace("e", "")
        filename = get_filename(extension)
        provided_filename = provided_filename.split(".")[0] + "." + extension
        if mime == "video/mp4":
            video_html = f"<video width='100%' controls>  <source src='public/image/{provided_filename}' type='video/mp4'>  </video>"
            resize_mp4(part.content, filename)
            collection.insert_one(
                {"username": f"{usr}", "message": f"{video_html}", "id": f"{uuid.uuid1().int}", "uid": f"{uid}"})
            uploads.insert_one({"provided": f"public/image/{provided_filename}", "stored": filename})
        elif mime == "image/gif":
            # If it is a gif add HTML img element to DB with path reference
            image_html = f"<div> <img src='public/image/{provided_filename}'> </div>"
            collection.insert_one(
                {"username": f"{usr}", "message": f"{image_html}", "id": f"{uuid.uuid1().int}", "uid": f"{uid}"})
            uploads.insert_one({"provided": f"public/image/{provided_filename}", "stored": filename})
            img = io.BytesIO(part.content)
            file = Image.open(img)
            # resize and save
            resize_gif(file, filename)

        elif mime == "image/jpeg" or mime == "image/png":
            # If it is a jpg or png add HTML img element to DB with path reference
            image_html = f"<div> <img src='public/image/{provided_filename}'> </div>"
            collection.insert_one(
                {"username": f"{usr}", "message": f"{image_html}", "id": f"{uuid.uuid1().int}", "uid": f"{uid}"})
            uploads.insert_one({"provided": f"public/image/{provided_filename}", "stored": filename})
            img = io.BytesIO(part.content)
            file = Image.open(img)
            # resize and save
            file.thumbnail((240, 240))
            file.save(filename)

    set_resp = ""
    response = f"HTTP/1.1 302 Found\r\nLocation: /{set_resp}".encode()
    handler.request.sendall(response)


def resize_mp4(file, filename):
    with open(filename, "wb") as f:
        f.write(file)
    f.close()

    # input = ffmpeg.input(filename)
    # video = input.video.filter('scale', '240:240:force_original_aspect_ratio=decrease')
    # audio = input.audio
    # out = ffmpeg.output()


def resize_gif(file, filename):
    images = []
    for frame in ImageSequence.Iterator(file):
        frame = frame.copy()
        frame.thumbnail((240, 240))
        images.append(frame)

    images[0].save(
        filename,
        save_all=True,
        append_images=images[1:],
        duration=500,
        loop=0
    )


def get_filename(extension):
    filename = str(uuid.uuid1().int)
    return f"public/image/image{filename}.{extension}"


def get_file(filename):
    files = uploads.find()
    for file in files:
        if file.get("provided") == filename:
            return file.get("stored")
    return filename
