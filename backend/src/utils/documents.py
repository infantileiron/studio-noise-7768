import hashlib
import json


def encode(document):
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def fingerprint(document):
    return hashlib.sha256(encode(document).encode()).hexdigest()
