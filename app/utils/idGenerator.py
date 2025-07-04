import hashlib
import random
import string

CHAR_SET = "OPQXYZabcqrstDEFGHIuvwxyz01234defghiRSTUVWjklmnop56789ABCJKLMN"


def genIdByEmail(input_value, length=32):
    hash_bytes = hashlib.sha256(input_value.encode()).digest()

    id_chars = []
    for byte in hash_bytes[:length]:
        id_chars.append(CHAR_SET[byte % len(CHAR_SET)])

    return ''.join(id_chars)


def generate_random_string(length=12):
    chars = string.ascii_letters + string.digits  # a-zA-Z0-9
    return ''.join(random.choice(chars) for _ in range(length))
