"""Append-only audit trail writes (isolated DB session so route transactions stay clean)."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import Request

from backend.app.core.database import AsyncSessionLocal
from backend.app.models import AuditLog

logger = logging.getLogger(__name__)


async def write_audit(
    *,
    user_id: Optional[UUID],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    try:
        async with AsyncSessionLocal() as session:
            log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=request.client.host if request and request.client else None,
                user_agent=request.headers.get("user-agent") if request else None,
            )
            session.add(log)
            await session.commit()
    except Exception as e:
        logger.warning("audit write skipped: %s", e)
