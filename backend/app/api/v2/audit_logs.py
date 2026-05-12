"""Query security audit trail for the authenticated user."""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core import get_current_user, get_db
from backend.app.models import AuditLog
from backend.app.schemas import AuditLogResponse

router = APIRouter(prefix="/api/v2/audit-logs", tags=["Audit"])


@router.get("", response_model=List[AuditLogResponse])
async def list_my_audit_logs(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    uid = UUID(current_user_id)
    r = await db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == uid)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = r.scalars().all()
    return [AuditLogResponse.model_validate(x) for x in rows]
