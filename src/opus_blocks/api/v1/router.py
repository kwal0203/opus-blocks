from fastapi import APIRouter

from opus_blocks.api.v1.routes.auth import router as auth_router
from opus_blocks.api.v1.routes.documents import router as documents_router
from opus_blocks.api.v1.routes.facts import router as facts_router
from opus_blocks.api.v1.routes.health import router as health_router
from opus_blocks.api.v1.routes.jobs import router as jobs_router
from opus_blocks.api.v1.routes.manuscripts import router as manuscripts_router
from opus_blocks.api.v1.routes.metrics import router as metrics_router
from opus_blocks.api.v1.routes.paragraphs import router as paragraphs_router
from opus_blocks.api.v1.routes.runs import router as runs_router
from opus_blocks.api.v1.routes.sentences import router as sentences_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(documents_router, tags=["documents"])
api_router.include_router(facts_router, tags=["facts"])
api_router.include_router(jobs_router, tags=["jobs"])
api_router.include_router(manuscripts_router, tags=["manuscripts"])
api_router.include_router(metrics_router, tags=["metrics"])
api_router.include_router(paragraphs_router, tags=["paragraphs"])
api_router.include_router(runs_router, tags=["runs"])
api_router.include_router(sentences_router, tags=["sentences"])
