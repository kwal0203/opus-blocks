import hashlib
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import jwt

from opus_blocks.core.config import settings


def _normalize_password(password: str) -> bytes:
    pwd_bytes = password.encode("utf-8")
    if len(pwd_bytes) > 72:
        return hashlib.sha256(pwd_bytes).digest()
    return pwd_bytes


def hash_password(password: str) -> str:
    pwd_bytes = _normalize_password(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    pwd_bytes = _normalize_password(password)
    return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))


def create_access_token(subject: str, email: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_exp_minutes)
    payload = {"sub": subject, "email": email, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
