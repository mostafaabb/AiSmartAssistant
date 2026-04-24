"""
Organization management routes for NexusAI API.
Handles team creation, member management, and org settings.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import logging

from backend.app.core import get_db, get_current_user
from backend.app.models import (
    Organization, OrganizationMember, User,
)
from backend.app.schemas import (
    OrganizationCreateRequest,
    OrganizationUpdateRequest,
    OrganizationResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/organizations", tags=["Organizations"])


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    request: OrganizationCreateRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new organization.

    Args:
        request: Organization creation data
        current_user_id: Current authenticated user ID
        db: Database session

    Returns:
        OrganizationResponse

    Raises:
        HTTPException 500: Failed to create organization
    """
    try:
        # Create organization
        org = Organization(
            name=request.name,
            description=request.description,
            owner_id=current_user_id,
        )

        db.add(org)
        await db.commit()
        await db.refresh(org)

        # Auto-add owner as member
        member = OrganizationMember(
            organization_id=org.id,
            user_id=current_user_id,
            role="owner",
        )
        db.add(member)
        await db.commit()

        logger.info(f"✅ Organization created: {org.id} ({org.name})")

        return OrganizationResponse.from_orm(org)

    except Exception as e:
        logger.error(f"Failed to create organization: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization"
        )


@router.get("", response_model=list)
async def list_organizations(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all organizations the user belongs to."""
    # Get organizations where user is member
    result = await db.execute(
        select(Organization).join(
            OrganizationMember,
            Organization.id == OrganizationMember.organization_id
        ).where(OrganizationMember.user_id == current_user_id)
    )
    orgs = result.scalars().all()

    # Also include organizations owned by user
    owner_result = await db.execute(
        select(Organization).where(Organization.owner_id == current_user_id)
    )
    owned_orgs = owner_result.scalars().all()

    all_orgs = list(set(orgs + owned_orgs))
    return [OrganizationResponse.from_orm(o) for o in all_orgs]


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get organization details."""
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    return OrganizationResponse.from_orm(org)


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    request: OrganizationUpdateRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update organization (admin only)."""
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Check if user is owner
    if org.owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owner can update"
        )

    if request.name:
        org.name = request.name
    if request.description:
        org.description = request.description

    await db.commit()
    await db.refresh(org)

    return OrganizationResponse.from_orm(org)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete organization (owner only)."""
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    if org.owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owner can delete"
        )

    await db.delete(org)
    await db.commit()

    logger.info(f"✅ Organization deleted: {org_id}")


@router.get("/{org_id}/members")
async def list_organization_members(
    org_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all members in organization."""
    # Get members
    result = await db.execute(
        select(OrganizationMember, User).join(
            User,
            OrganizationMember.user_id == User.id
        ).where(OrganizationMember.organization_id == org_id)
    )
    members = result.all()

    return [
        {
            "user_id": str(member[1].id),
            "email": member[1].email,
            "username": member[1].username,
            "role": member[0].role,
            "joined_at": member[0].joined_at.isoformat() if member[0].joined_at else None,
        }
        for member in members
    ]


@router.post("/{org_id}/members/{user_id}")
async def add_organization_member(
    org_id: UUID,
    user_id: str,
    role: str = "member",
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add member to organization (admin only)."""
    # Check if org exists and user is admin
    org_result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = org_result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    if org.owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owner can add members"
        )

    # Check if user exists
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    if not user_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if already a member
    member_result = await db.execute(
        select(OrganizationMember).where(
            (OrganizationMember.organization_id == org_id) &
            (OrganizationMember.user_id == user_id)
        )
    )
    if member_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already a member of organization"
        )

    # Add member
    member = OrganizationMember(
        organization_id=org_id,
        user_id=user_id,
        role=role,
    )
    db.add(member)
    await db.commit()

    logger.info(f"✅ User {user_id} added to organization {org_id}")

    return {"message": "User added to organization"}


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_organization_member(
    org_id: UUID,
    user_id: str,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove member from organization (admin only)."""
    # Check if org exists and user is admin
    org_result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = org_result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    if org.owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owner can remove members"
        )

    # Get member
    member_result = await db.execute(
        select(OrganizationMember).where(
            (OrganizationMember.organization_id == org_id) &
            (OrganizationMember.user_id == user_id)
        )
    )
    member = member_result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    # Prevent removing owner
    if member.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove organization owner"
        )

    await db.delete(member)
    await db.commit()

    logger.info(f"✅ User {user_id} removed from organization {org_id}")
