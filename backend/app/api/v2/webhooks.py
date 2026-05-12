"""Organization webhooks (signed outbound HTTPS notifications)."""

from __future__ import annotations

import secrets
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core import get_current_user, get_db
from backend.app.models import Organization, OrganizationMember, Webhook
from backend.app.schemas import (
    WebhookCreateRequest,
    WebhookCreatedResponse,
    WebhookResponse,
    WebhookUpdateRequest,
)

router = APIRouter(prefix="/api/v2/organizations", tags=["Webhooks"])


async def _can_manage_webhooks(db: AsyncSession, user_id: str, org_id: UUID) -> bool:
    uid = UUID(user_id)
    org = await db.get(Organization, org_id)
    if not org:
        return False
    if org.owner_id == uid:
        return True
    r = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == uid,
            OrganizationMember.role.in_(["owner", "admin"]),
        )
    )
    return r.scalar_one_or_none() is not None


def _hint(secret: str) -> str:
    if len(secret) >= 4:
        return "…" + secret[-4:]
    return "****"


@router.post("/{org_id}/webhooks", response_model=WebhookCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    org_id: UUID,
    body: WebhookCreateRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await _can_manage_webhooks(db, current_user_id, org_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    signing = "whsec_" + secrets.token_hex(24)
    row = Webhook(
        organization_id=org_id,
        created_by_id=UUID(current_user_id),
        url=body.url,
        secret=signing,
        events=body.events or [],
        description=body.description,
        is_active=True,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    base = WebhookResponse(
        id=row.id,
        organization_id=row.organization_id,
        url=row.url,
        events=row.events or [],
        description=row.description,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
        secret_hint=_hint(signing),
    )
    return WebhookCreatedResponse(**base.model_dump(), signing_secret=signing)


@router.get("/{org_id}/webhooks", response_model=List[WebhookResponse])
async def list_webhooks(
    org_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await _can_manage_webhooks(db, current_user_id, org_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    r = await db.execute(select(Webhook).where(Webhook.organization_id == org_id).order_by(Webhook.created_at.desc()))
    rows = r.scalars().all()
    return [
        WebhookResponse(
            id=w.id,
            organization_id=w.organization_id,
            url=w.url,
            events=w.events or [],
            description=w.description,
            is_active=w.is_active,
            created_at=w.created_at,
            updated_at=w.updated_at,
            secret_hint=_hint(w.secret),
        )
        for w in rows
    ]


@router.patch("/{org_id}/webhooks/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    org_id: UUID,
    webhook_id: UUID,
    body: WebhookUpdateRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await _can_manage_webhooks(db, current_user_id, org_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    r = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id, Webhook.organization_id == org_id)
    )
    w = r.scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    if body.url is not None:
        w.url = body.url
    if body.events is not None:
        w.events = body.events
    if body.description is not None:
        w.description = body.description
    if body.is_active is not None:
        w.is_active = body.is_active

    await db.commit()
    await db.refresh(w)
    return WebhookResponse(
        id=w.id,
        organization_id=w.organization_id,
        url=w.url,
        events=w.events or [],
        description=w.description,
        is_active=w.is_active,
        created_at=w.created_at,
        updated_at=w.updated_at,
        secret_hint=_hint(w.secret),
    )


@router.delete("/{org_id}/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    org_id: UUID,
    webhook_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await _can_manage_webhooks(db, current_user_id, org_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    r = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id, Webhook.organization_id == org_id)
    )
    w = r.scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
    await db.delete(w)
    await db.commit()
    return None
