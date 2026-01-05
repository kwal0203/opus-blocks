from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from opus_blocks.core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(password, hashed_password)


def create_access_token(subject: str, email: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_exp_minutes)
    payload = {"sub": subject, "email": email, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
