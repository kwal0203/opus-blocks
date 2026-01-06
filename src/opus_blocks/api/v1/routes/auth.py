from fastapi import APIRouter, HTTPException, status

from opus_blocks.api.deps import DbSession
from opus_blocks.core.config import settings
from opus_blocks.core.rate_limit import rate_limit
from opus_blocks.schemas.user import Token, UserCreate, UserLogin, UserRead
from opus_blocks.services.auth import (
    authenticate_user,
    create_user,
    get_user_by_email,
    issue_access_token,
)

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@rate_limit(settings.rate_limit_auth)
async def register(user_in: UserCreate, session: DbSession) -> UserRead:
    existing = await get_user_by_email(session, user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    user = await create_user(session, user_in.email, user_in.password)
    return UserRead.model_validate(user)


@router.post("/login", response_model=Token)
@rate_limit(settings.rate_limit_auth)
async def login(user_in: UserLogin, session: DbSession) -> Token:
    user = await authenticate_user(session, user_in.email, user_in.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = issue_access_token(user)
    return Token(access_token=token)
