from fastapi import FastAPI

from opus_blocks.api.v1.router import api_router
from opus_blocks.core.config import settings
from opus_blocks.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging(settings.environment)

    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
