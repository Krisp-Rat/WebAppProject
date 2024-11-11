import base64
import hashlib


class Frame:
    def __init__(self, fin_bit, opcode, payload_length, payload):
        self.fin_bit = fin_bit
        self.opcode = opcode
        self.payload_length = payload_length
        self.payload = payload


def compute_accept(key):
    key = key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    hash = hashlib.sha1(key.encode()).digest()
    accept = base64.b64encode(hash).decode()
    return accept


def parse_ws_frame(input_bytes):
    fin_bit = (input_bytes[0] & 128) >> 7
    opcode = input_bytes[0] & 15
    mask_bit = (input_bytes[1] & 128) >> 7
    payload_length = input_bytes[1] & 126
    pointer = 2
    if payload_length == 126:
        payload_length = int.from_bytes(input_bytes[2:4])
        pointer = 4
    elif payload_length == 127:
        payload_length = int.from_bytes(input_bytes[2:10])
        pointer = 10
    payload = b'' * payload_length
    if mask_bit == 1:
        mask = input_bytes[pointer: pointer + 4]
        pointer += 4
        extra = payload_length % 4
        for i in range(0, payload_length - extra, 4):
            payload = int.from_bytes(input_bytes[pointer + i: pointer + i + 4]) ^ int.from_bytes(mask)
        if extra != 0:
            oped = int.from_bytes(input_bytes[payload_length - extra: payload_length]) ^ int.from_bytes(mask[0:extra])
            payload[payload_length - extra: payload_length] = (oped)

    else:
        payload = input_bytes[pointer: pointer + payload_length]

    return Frame(fin_bit, opcode, payload_length, payload)


def generate_ws_frame(input_bytes):
    frame_bytes = b''

    return frame_bytes


mask_bites = b'\xa1\xb2\xc3\xd4'
pre_payload = b'\xf9\xe8\xd7\xc6\xb5\xa4'


input_bytes = b'\x02\x06\x10\x10\xe1\xa3\x13\x04'
frame = parse_ws_frame(input_bytes)
if frame.payload_length != 6:
    print("Invalid payload length")
if frame.opcode != 2:
    print("Invalid opcode: ", frame.opcode)
if frame.fin_bit != 0:
    print("Invalid fin_bit", frame.fin_bit)
if frame.payload_length != len(frame.payload):
    print("Invalid payload")

print(frame.payload)
