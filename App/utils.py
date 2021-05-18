import hashlib


def string_encode(string):
    return str(int(hashlib.md5(str(string).encode('utf-8')).hexdigest(), 16))


def doc_key_error(field_name):
    raise KeyError("Document must contain '{}' field.".format(field_name))
