import hashlib

CHAR_SET = "OPQXYZabcqrstDEFGHIuvwxyz01234defghiRSTUVWjklmnop56789ABCJKLMN"


def genIdByEmail(input_value, length=32):
    hash_bytes = hashlib.sha256(input_value.encode()).digest()

    id_chars = []
    for byte in hash_bytes[:length]:
        id_chars.append(CHAR_SET[byte % len(CHAR_SET)])

    return ''.join(id_chars)


unique_id = genIdByEmail("kasun@exampleasdasdasd.com")  # Input that never changes
print("Unique ID:", unique_id)
