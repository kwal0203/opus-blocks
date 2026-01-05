from fastapi import APIRouter

from opus_blocks.api.v1.routes.auth import router as auth_router
from opus_blocks.api.v1.routes.documents import router as documents_router
from opus_blocks.api.v1.routes.health import router as health_router
from opus_blocks.api.v1.routes.jobs import router as jobs_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(documents_router, tags=["documents"])
api_router.include_router(jobs_router, tags=["jobs"])
