from util.request import Request


def extract_credentials(request):
    body = request.body.decode('utf-8')
    username, password = body.split('&', 1)
    usr = username[9:]
    passwd = password[9:]
    passwd = percent_characters(passwd)
    return [usr, passwd]


def validate_password(passwd):
    # Password must be at least 8 chars long
    if len(passwd) < 8:
        return False
    # Must have one lowercase and one uppercase
    all_caps = passwd.upper()
    all_lowers = passwd.lower()
    if passwd == all_caps or passwd == all_lowers:
        return False

    # Password must contain at least one char
    if not valid_chars(passwd):
        return False
    return True


def percent_characters(passwd):
    chars = {'%21': "!", '%40': '@', '%23': '#', '%24': '$', '%5E': '^', '%26': '&', '%28': '(', "%29": ')', '%3D': '='}
    for key, value in chars.items():
        if key in passwd:
            passwd = passwd.replace(key, value)
    if "%25" in passwd:
        passwd = passwd.replace("%25", "%")
    return passwd


def valid_chars(passwd):
    special = ['!', '@', '#', '$', '%', '^', '&', '(', ')', '-', '_', '=']
    numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    alpha = "abcdefghijklmnopqrstuvwxyz"
    lower = passwd.lower()
    spec = False
    nums = False
    let = False
    diff = True
    for i in lower:
        if i in special:
            spec = True
        elif i in numbers:
            nums = True
        elif i in alpha:
            let = True
        else:
            diff = False

    return spec and nums and let and diff



