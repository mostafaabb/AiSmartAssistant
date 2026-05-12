"""Aggregated usage metrics for dashboards and billing previews."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core import get_current_user, get_db
from backend.app.models import AuditLog, CodeExecution, Project
from backend.app.schemas import UsageMetricsResponse

router = APIRouter(prefix="/api/v2/usage", tags=["Usage"])


@router.get("/metrics", response_model=UsageMetricsResponse)
async def usage_metrics(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    hours: int = Query(24, ge=1, le=168),
):
    uid = UUID(current_user_id)
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    ar = await db.execute(
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.user_id == uid, AuditLog.created_at >= since)
    )
    audit_events = int(ar.scalar() or 0)

    er = await db.execute(
        select(func.count())
        .select_from(CodeExecution)
        .join(Project, CodeExecution.project_id == Project.id)
        .where(Project.created_by_id == uid, CodeExecution.created_at >= since)
    )
    code_executions = int(er.scalar() or 0)

    return UsageMetricsResponse(
        period_hours=hours,
        audit_events=audit_events,
        code_executions=code_executions,
    )
