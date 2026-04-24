"""
Git integration routes for NexusAI API.
Handles repository operations: clone, commit, push, pull, branches.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from backend.app.core import get_db, get_current_user
from backend.app.models import Project
from backend.app.services.git_service import git_service
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/projects", tags=["Git"])


@router.post("/{project_id}/git/clone")
async def clone_repository(
    project_id: UUID,
    git_url: str,
    branch: str = "main",
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Clone a Git repository.

    Args:
        project_id: Target project
        git_url: Repository URL
        branch: Branch to clone (default: main)
        current_user_id: Current user ID
        db: Database session

    Returns:
        Result with status message
    """
    # Verify project exists and user has access
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Clone repository
    clone_result = await git_service.clone_repository(
        str(project_id),
        git_url,
        branch,
    )

    if clone_result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=clone_result["message"]
        )

    # Update project with git info
    project.git_url = git_url
    project.git_branch = branch
    await db.commit()

    return clone_result


@router.post("/{project_id}/git/commit")
async def commit_changes(
    project_id: UUID,
    message: str,
    author_name: str = "NexusAI User",
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Commit staged changes.

    Args:
        project_id: Target project
        message: Commit message
        author_name: Author name
        current_user_id: Current user ID
        db: Database session

    Returns:
        Commit result
    """
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    commit_result = await git_service.commit(
        str(project_id),
        message,
        author_name,
    )

    return commit_result


@router.post("/{project_id}/git/push")
async def push_changes(
    project_id: UUID,
    branch: str = "main",
    token: str = None,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Push commits to remote.

    Args:
        project_id: Target project
        branch: Branch to push
        token: GitHub token for auth (optional)
        current_user_id: Current user ID
        db: Database session

    Returns:
        Push result
    """
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    push_result = await git_service.push(str(project_id), branch, token)
    return push_result


@router.post("/{project_id}/git/pull")
async def pull_changes(
    project_id: UUID,
    branch: str = "main",
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pull changes from remote."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    pull_result = await git_service.pull(str(project_id), branch)
    return pull_result


@router.get("/{project_id}/git/branches")
async def list_branches(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all branches.

    Returns:
        List of branch names
    """
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    branches = await git_service.list_branches(str(project_id))
    return {"branches": branches}


@router.post("/{project_id}/git/checkout")
async def checkout_branch(
    project_id: UUID,
    branch: str,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Checkout a branch."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    checkout_result = await git_service.checkout_branch(str(project_id), branch)
    return checkout_result


@router.get("/{project_id}/git/status")
async def get_git_status(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get git status (modified files, current branch).

    Returns:
        Status information
    """
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    status = await git_service.get_status(str(project_id))
    return status
