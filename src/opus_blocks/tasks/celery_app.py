from celery import Celery

from opus_blocks.core.config import settings

celery_app = Celery(
    "opus_blocks",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.task_track_started = True
celery_app.conf.task_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.result_serializer = "json"
