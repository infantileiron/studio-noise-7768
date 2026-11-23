import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from src.config.runtime import JWT_SECRET


def password_hash(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 250_000)
    return f'{salt}:{digest.hex()}'


def verify_password(password, stored):
    salt, expected = stored.split(':')
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 250_000)
    return hmac.compare_digest(digest.hex(), expected)


def make_token(account):
    return jwt.encode({
        'sub': str(account['id']), 'exp': datetime.now(timezone.utc) + timedelta(hours=8),
        'iss': 'studio-noise',
    }, JWT_SECRET, algorithm='HS256')


def token_subject(token):
    payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'], issuer='studio-noise',
                         options={'require': ['sub', 'exp', 'iss']})
    return int(payload['sub'])
