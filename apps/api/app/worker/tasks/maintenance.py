from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import delete, func, select

from app.db.session import sync_session
from app.integrations.factory import all_adapters
from app.models.catalog import Course, CourseModule, Lesson
from app.models.enums import IntegrationHealth, IntegrationKind
from app.models.system import IntegrationStatus
from app.models.user import RefreshToken
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.worker.tasks.maintenance.run_integration_healthchecks")
def run_integration_healthchecks() -> dict:
    now = datetime.now(UTC)
    results: dict[str, str] = {}

    with sync_session() as db:
        for adapter in all_adapters():
            provider = getattr(adapter, "provider_name", "unknown")
            kind = getattr(adapter, "kind", IntegrationKind.video)
            try:
                ok, error = asyncio.run(adapter.healthcheck())
            except Exception as exc:
                ok, error = False, str(exc)

            row = db.scalar(
                select(IntegrationStatus).where(
                    IntegrationStatus.kind == kind,
                    IntegrationStatus.provider == provider,
                )
            )
            if row is None:
                row = IntegrationStatus(
                    provider=provider,
                    display_name=getattr(adapter, "display_name", provider),
                    kind=kind,
                    consecutive_failures=0,
                )
                db.add(row)

            row.is_enabled = adapter.is_configured()
            if ok:
                row.health = IntegrationHealth.ok
                row.last_success_at = now
                row.consecutive_failures = 0
                row.last_error_message = None
            else:
                row.health = (
                    IntegrationHealth.disabled
                    if not adapter.is_configured()
                    else IntegrationHealth.error
                )
                row.last_error_at = now
                row.last_error_message = (error or "")[:1000]
                row.consecutive_failures = (row.consecutive_failures or 0) + 1

            results[f"{kind.value}:{provider}"] = row.health.value

        db.commit()

    logger.info("Integratsiya healthcheck: %s", results)
    return results


@celery_app.task(name="app.worker.tasks.maintenance.cleanup_expired_tokens")
def cleanup_expired_tokens() -> dict:
    with sync_session() as db:
        result = db.execute(delete(RefreshToken).where(RefreshToken.expires_at < datetime.now(UTC)))
        db.commit()
        return {"deleted": result.rowcount or 0}


@celery_app.task(name="app.worker.tasks.maintenance.recalculate_all_course_stats")
def recalculate_all_course_stats() -> dict:
    with sync_session() as db:
        courses = db.scalars(select(Course)).all()
        for course in courses:
            totals = db.execute(
                select(
                    func.count(Lesson.id),
                    func.coalesce(func.sum(Lesson.duration_seconds), 0),
                )
                .select_from(Lesson)
                .join(CourseModule, Lesson.module_id == CourseModule.id)
                .where(CourseModule.course_id == course.id, Lesson.is_published.is_(True))
            ).one()
            course.lessons_count = int(totals[0] or 0)
            course.duration_seconds = int(totals[1] or 0)
        db.commit()
        return {"courses": len(courses)}
