from celery import Celery
from celery.schedules import crontab
from app.config.dependencies import get_settings

settings = get_settings()

celery_app = Celery(
    "cinema",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.email_tasks", "app.tasks.cleanup_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    result_expires=3600,  # 1 hour
)

# Celery Beat schedule
celery_app.conf.beat_schedule = {
    "cleanup-expired-tokens-every-hour": {
        "task": "app.tasks.cleanup_tasks.cleanup_expired_tokens",
        "schedule": crontab(minute=0, hour="*/1"),  # Every hour
    },
}

if __name__ == "__main__":
    celery_app.start()
