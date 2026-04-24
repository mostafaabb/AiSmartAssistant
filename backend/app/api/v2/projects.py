"""
Project management routes for NexusAI API.
Handles project CRUD operations and member management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List
import logging

from backend.app.core import get_db, get_current_user
from backend.app.models import Project, ProjectMember, Organization, User
from backend.app.schemas import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    org_id: UUID,
    request: ProjectCreateRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new project in an organization.

    Args:
        org_id: Organization ID
        request: Project creation data
        current_user_id: Current authenticated user ID
        db: Database session

    Returns:
        ProjectResponse

    Raises:
        HTTPException 403: User not member of organization
        HTTPException 404: Organization not found
    """
    # Verify organization exists and user is member
    org_result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = org_result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Check if user is member of organization
    member_result = await db.execute(
        select(ProjectMember).where(
            (ProjectMember.project_id == org_id) &
            (ProjectMember.user_id == current_user_id)
        )
    )
    if not member_result.scalar_one_or_none():
        # Check org membership instead
        from backend.app.models import OrganizationMember
        org_member = await db.execute(
            select(OrganizationMember).where(
                (OrganizationMember.organization_id == org_id) &
                (OrganizationMember.user_id == current_user_id)
            )
        )
        if not org_member.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not member of organization"
            )

    # Create project
    project = Project(
        organization_id=org_id,
        name=request.name,
        description=request.description,
        git_url=request.git_url,
        created_by_id=current_user_id,
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    logger.info(f"✅ Project created: {project.id} ({project.name})")

    return ProjectResponse.from_orm(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a project by ID."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return ProjectResponse.from_orm(project)


@router.get("")
async def list_projects(
    org_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects in an organization."""
    result = await db.execute(
        select(Project).where(Project.organization_id == org_id)
    )
    projects = result.scalars().all()

    return [ProjectResponse.from_orm(p) for p in projects]


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    request: ProjectUpdateRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Verify user is project owner
    if project.created_by_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can update"
        )

    if request.name:
        project.name = request.name
    if request.description:
        project.description = request.description

    await db.commit()
    await db.refresh(project)

    return ProjectResponse.from_orm(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    if project.created_by_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can delete"
        )

    await db.delete(project)
    await db.commit()

    logger.info(f"✅ Project deleted: {project_id}")
