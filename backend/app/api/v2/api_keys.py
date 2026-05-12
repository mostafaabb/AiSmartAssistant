"""Programmatic API keys for automation (CI, scripts, integrations)."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core import get_current_user, get_db
from backend.app.models import ApiKey, OrganizationMember
from backend.app.schemas import (
    ApiKeyCreateRequest,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
)
from backend.app.services.api_key_service import hash_api_key, invalidate_api_key_cache_by_hash

router = APIRouter(prefix="/api/v2/developers/api-keys", tags=["API Keys"])


async def _ensure_org_member(db: AsyncSession, user_id: str, org_id: UUID) -> None:
    r = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == UUID(user_id),
        )
    )
    if not r.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )


@router.post("", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: ApiKeyCreateRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.organization_id:
        await _ensure_org_member(db, current_user_id, body.organization_id)

    plain = "nxai_" + secrets.token_urlsafe(32)
    digest = hash_api_key(plain)
    prefix = plain[:14] + "…"
    scopes = body.scopes if body.scopes else ["read", "write"]
    expires = None
    if body.expires_in_days:
        expires = datetime.now(timezone.utc) + timedelta(days=body.expires_in_days)

    row = ApiKey(
        user_id=UUID(current_user_id),
        organization_id=body.organization_id,
        name=body.name,
        key_hash=digest,
        prefix_display=prefix,
        scopes=scopes,
        expires_at=expires,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    base = ApiKeyResponse.model_validate(row)
    return ApiKeyCreatedResponse(**base.model_dump(), api_key=plain)


@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == UUID(current_user_id))
        .order_by(ApiKey.created_at.desc())
    )
    rows = r.scalars().all()
    return [ApiKeyResponse.model_validate(x) for x in rows]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.user_id == UUID(current_user_id),
        )
    )
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    row.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    await invalidate_api_key_cache_by_hash(row.key_hash)
    return None
