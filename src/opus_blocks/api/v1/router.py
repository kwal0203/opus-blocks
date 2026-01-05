from fastapi import APIRouter

from opus_blocks.api.v1.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
