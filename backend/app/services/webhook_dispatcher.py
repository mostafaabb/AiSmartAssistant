"""Deliver signed webhook payloads to subscriber URLs (background-friendly)."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx
from sqlalchemy import select

from backend.app.core.database import AsyncSessionLocal
from backend.app.models import Webhook

logger = logging.getLogger(__name__)


def _sign_body(secret: str, body_bytes: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()


async def deliver_organization_event(
    organization_id: uuid.UUID,
    event_type: str,
    data: Dict[str, Any],
) -> None:
    """Load active webhooks for an org and POST signed JSON (best-effort, logs failures)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Webhook).where(
                Webhook.organization_id == organization_id,
                Webhook.is_active.is_(True),
            )
        )
        hooks: List[Webhook] = list(result.scalars().all())

    if not hooks:
        return

    event_id = str(uuid.uuid4())
    created = datetime.now(timezone.utc).isoformat()
    envelope = {
        "id": event_id,
        "type": event_type,
        "created": created,
        "data": data,
    }
    body_bytes = json.dumps(envelope, separators=(",", ":"), default=str).encode("utf-8")

    async with httpx.AsyncClient(timeout=httpx.Timeout(12.0)) as client:
        for hook in hooks:
            events = hook.events or []
            if events and event_type not in events:
                continue
            sig = _sign_body(hook.secret, body_bytes)
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "NexusAI-Webhooks/1.0",
                "X-NexusAI-Event": event_type,
                "X-NexusAI-Delivery": event_id,
                "X-NexusAI-Signature": f"v1={sig}",
            }
            try:
                resp = await client.post(hook.url, content=body_bytes, headers=headers)
                if resp.status_code >= 400:
                    logger.warning(
                        "webhook delivery failed status=%s url=%s",
                        resp.status_code,
                        hook.url[:80],
                    )
            except Exception as e:
                logger.warning("webhook delivery error url=%s err=%s", hook.url[:80], e)
