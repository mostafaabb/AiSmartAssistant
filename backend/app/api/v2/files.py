"""
File management routes for NexusAI API.
Handles file CRUD and version history.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import logging

from backend.app.core import get_db, get_current_user
from backend.app.models import ProjectFile, FileVersion, Project
from backend.app.schemas import (
    FileCreateRequest,
    FileUpdateRequest,
    FileResponse,
    FileVersionResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/projects", tags=["Files"])


@router.post("/{project_id}/files", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def create_file(
    project_id: UUID,
    request: FileCreateRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new file in a project."""
    # Verify project exists
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check if file already exists
    existing = await db.execute(
        select(ProjectFile).where(
            (ProjectFile.project_id == project_id) &
            (ProjectFile.path == request.path)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File already exists"
        )

    # Create file
    file = ProjectFile(
        project_id=project_id,
        path=request.path,
        content=request.content,
        language=request.language,
        created_by_id=current_user_id,
    )

    db.add(file)
    await db.commit()
    await db.refresh(file)

    logger.info(f"✅ File created: {request.path}")

    return FileResponse.from_orm(file)


@router.get("/{project_id}/files")
async def list_files(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all files in a project."""
    result = await db.execute(
        select(ProjectFile).where(ProjectFile.project_id == project_id)
    )
    files = result.scalars().all()

    return [FileResponse.from_orm(f) for f in files]


@router.get("/{project_id}/files/{file_id}", response_model=FileResponse)
async def get_file(
    project_id: UUID,
    file_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific file."""
    result = await db.execute(
        select(ProjectFile).where(
            (ProjectFile.id == file_id) &
            (ProjectFile.project_id == project_id)
        )
    )
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return FileResponse.from_orm(file)


@router.put("/{project_id}/files/{file_id}", response_model=FileResponse)
async def update_file(
    project_id: UUID,
    file_id: UUID,
    request: FileUpdateRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update file content."""
    result = await db.execute(
        select(ProjectFile).where(
            (ProjectFile.id == file_id) &
            (ProjectFile.project_id == project_id)
        )
    )
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Create version history entry
    old_content = file.content
    version = FileVersion(
        file_id=file_id,
        content=old_content,
        created_by_id=current_user_id,
        commit_message=request.commit_message,
    )

    file.content = request.content

    db.add(version)
    await db.commit()
    await db.refresh(file)

    logger.info(f"✅ File updated: {file.path}")

    return FileResponse.from_orm(file)


@router.delete("/{project_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    project_id: UUID,
    file_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a file."""
    result = await db.execute(
        select(ProjectFile).where(
            (ProjectFile.id == file_id) &
            (ProjectFile.project_id == project_id)
        )
    )
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    await db.delete(file)
    await db.commit()

    logger.info(f"✅ File deleted: {file.path}")


@router.get("/{project_id}/files/{file_id}/versions")
async def get_file_versions(
    project_id: UUID,
    file_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get file version history."""
    result = await db.execute(
        select(FileVersion).where(FileVersion.file_id == file_id)
    )
    versions = result.scalars().all()

    return [FileVersionResponse.from_orm(v) for v in versions]


@router.post("/{project_id}/files/{file_id}/versions/{version_id}/restore", response_model=FileResponse)
async def restore_file_version(
    project_id: UUID,
    file_id: UUID,
    version_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restore a file to a previous version."""
    # Get the version
    version_result = await db.execute(
        select(FileVersion).where(FileVersion.id == version_id)
    )
    version = version_result.scalar_one_or_none()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )

    # Get the file
    file_result = await db.execute(
        select(ProjectFile).where(ProjectFile.id == file_id)
    )
    file = file_result.scalar_one_or_none()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Save current version before restoring
    current_version = FileVersion(
        file_id=file_id,
        content=file.content,
        created_by_id=current_user_id,
        commit_message="Auto-backup before restore",
    )

    file.content = version.content
    db.add(current_version)
    await db.commit()
    await db.refresh(file)

    logger.info(f"✅ File restored to version: {version_id}")

    return FileResponse.from_orm(file)
