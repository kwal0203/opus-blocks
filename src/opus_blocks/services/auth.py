from opus_blocks.core.security import hash_password, verify_password


def build_password_hash(password: str) -> str:
    return hash_password(password)


def check_password(password: str, hashed_password: str) -> bool:
    return verify_password(password, hashed_password)
