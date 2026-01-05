from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.core.security import create_access_token, hash_password, verify_password
from opus_blocks.models.user import User


def build_password_hash(password: str) -> str:
    return hash_password(password)


def check_password(password: str, hashed_password: str) -> bool:
    return verify_password(password, hashed_password)


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, email: str, password: str) -> User:
    user = User(email=email, password_hash=hash_password(password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(session, email)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def issue_access_token(user: User) -> str:
    return create_access_token(str(user.id), user.email)
