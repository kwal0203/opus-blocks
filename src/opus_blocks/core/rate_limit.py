from collections.abc import Callable
from typing import TypeVar, cast

from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import Response

from opus_blocks.core.config import settings

T = TypeVar("T", bound=Callable[..., object])

_limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.rate_limit_storage_uri,
    enabled=settings.rate_limit_enabled,
)


def get_limiter() -> Limiter:
    return _limiter


def rate_limit(limit: str) -> Callable[[T], T]:
    if not settings.rate_limit_enabled:

        def _decorator(func: T) -> T:
            return func

        return _decorator
    return _limiter.limit(limit)


def _handle_rate_limit(request: Request, exc: Exception) -> Response:
    return _rate_limit_exceeded_handler(request, cast(RateLimitExceeded, exc))


def apply_rate_limiting(app: FastAPI) -> None:
    if not settings.rate_limit_enabled:
        return
    app.state.limiter = _limiter
    app.add_exception_handler(RateLimitExceeded, _handle_rate_limit)
    app.add_middleware(SlowAPIMiddleware)
