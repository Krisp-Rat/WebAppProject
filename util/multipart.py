
def parse_multipart(request):
    # The value of the boundary from the Content-Type header as a string
    boundary = ""
    headers = ""
    name = ""
    content = b""

    return boundary, [headers, name, content]

