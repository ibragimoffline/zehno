from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

import app.models  # noqa: F401
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()

celery_app = Celery(
    "zehno",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=[
        "app.worker.tasks.certificates",
        "app.worker.tasks.crm",
        "app.worker.tasks.notifications",
        "app.worker.tasks.video",
        "app.worker.tasks.maintenance",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Tashkent",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=900,
    task_soft_time_limit=840,
    worker_max_tasks_per_child=200,
    worker_prefetch_multiplier=4,
    broker_connection_retry_on_startup=True,
    task_default_retry_delay=30,
    task_acks_late=True,
    result_expires=3600 * 24,
)

celery_app.conf.beat_schedule = {
    "daily-learning-reminders": {
        "task": "app.worker.tasks.notifications.send_learning_reminders",
        "schedule": crontab(hour=19, minute=0),
    },
    "weekly-b2b-reports": {
        "task": "app.worker.tasks.notifications.send_weekly_b2b_reports",
        "schedule": crontab(day_of_week=1, hour=9, minute=0),
    },
    "integration-healthchecks": {
        "task": "app.worker.tasks.maintenance.run_integration_healthchecks",
        "schedule": crontab(minute="*/10"),
    },
    "cleanup-expired-tokens": {
        "task": "app.worker.tasks.maintenance.cleanup_expired_tokens",
        "schedule": crontab(hour=3, minute=0),
    },
    "retry-failed-crm-syncs": {
        "task": "app.worker.tasks.crm.retry_failed_syncs",
        "schedule": crontab(minute="*/5"),
    },
}
