import base64
import hashlib


class Frame:
    def __init__(self, fin_bit, opcode, payload_length, payload, total_length):
        self.fin_bit = fin_bit
        self.opcode = opcode
        self.payload_length = payload_length
        self.payload = payload
        self.total_length = total_length


def compute_accept(key):
    key = key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    hash = hashlib.sha1(key.encode()).digest()
    accept = base64.b64encode(hash).decode()
    return accept


def parse_ws_frame(input_bytes):
    fin_bit = (input_bytes[0] & 128) >> 7
    opcode = input_bytes[0] & 15
    mask_bit = (input_bytes[1] & 128) >> 7
    payload_length = input_bytes[1] & 127
    pointer = 2
    if payload_length == 126:
        payload_length = int.from_bytes(input_bytes[2:4])
        pointer += 2
    elif payload_length == 127:
        payload_length = int.from_bytes(input_bytes[2:10])
        pointer += 8
    payload = b''
    if mask_bit == 1:
        mask = input_bytes[pointer: pointer + 4]
        pointer += 4
        for i in range(payload_length):
            bites = input_bytes[pointer + i] ^ mask[i % 4]
            payload += bites.to_bytes(1)

    else:
        payload = input_bytes[pointer: pointer + payload_length]
        pointer += payload_length

    return Frame(fin_bit, opcode, payload_length, payload, pointer)


def generate_ws_frame(input_bytes):
    payload_length = len(input_bytes)
    if payload_length < 126:
        length_bit = payload_length.to_bytes()
    elif payload_length < 65536:
        length_bit = b'\x7E' + payload_length.to_bytes(length=2)
    else:
        length_bit = b'\x7F' + payload_length.to_bytes(length=8)
    frame_bytes = b'\x81' + length_bit + input_bytes
    return frame_bytes


def read_length(input_bytes):
    mask_bit = (input_bytes[1] & 128) >> 7
    payload_length = input_bytes[1] & 127
    header = 2
    if payload_length == 126:
        payload_length = int.from_bytes(input_bytes[2:4])
        header += 2
    elif payload_length == 127:
        payload_length = int.from_bytes(input_bytes[2:10])
        header += 8
    if mask_bit == 1:
        header += 4
    return payload_length + header


def test1():
    input = b"\x81\xfe\x0c\32\xaa\x1b\xe2\x23\xe1"
    parsed = read_length(input)
    print(parsed)

# test1()
