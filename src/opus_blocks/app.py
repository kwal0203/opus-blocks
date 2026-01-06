from fastapi import FastAPI

from opus_blocks.api.v1.router import api_router
from opus_blocks.core.config import settings
from opus_blocks.core.logging import configure_logging
from opus_blocks.core.rate_limit import apply_rate_limiting


def create_app() -> FastAPI:
    configure_logging(settings.environment)

    app = FastAPI(title=settings.app_name, version=settings.app_version)
    apply_rate_limiting(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
