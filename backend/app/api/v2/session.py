"""
Session management routes for NexusAI API.
Handles user session state (chat history, code context, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime, timedelta
import logging

from backend.app.core import get_db, get_current_user, settings
from backend.app.models import Session as SessionModel
from backend.app.schemas import (
    SessionResponse,
    SessionUpdateRequest,
    ChatMessage,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/session", tags=["Session"])


@router.post("/create", response_model=SessionResponse)
async def create_session(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user session for a project.

    Args:
        project_id: Project ID to associate with session
        current_user_id: Current authenticated user ID
        db: Database session

    Returns:
        SessionResponse

    Raises:
        HTTPException 404: Project not found
    """
    # Verify project exists
    from backend.app.models import Project
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Set session expiration to 24 hours from now
    expires_at = datetime.utcnow() + timedelta(hours=24)

    # Create session
    session = SessionModel(
        user_id=current_user_id,
        project_id=project_id,
        code_context={},
        chat_history=[],
        expires_at=expires_at,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    logger.info(f"✅ Session created: {session.id}")

    return SessionResponse.from_orm(session)


@router.get("/current", response_model=SessionResponse)
async def get_current_session(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get or create current user session for a project.

    Args:
        project_id: Project ID
        current_user_id: Current user ID
        db: Database session

    Returns:
        SessionResponse (existing or new session)
    """
    # Try to get existing session
    result = await db.execute(
        select(SessionModel).where(
            (SessionModel.user_id == current_user_id) &
            (SessionModel.project_id == project_id)
        )
    )
    session = result.scalar_one_or_none()

    # If exists and not expired, return it
    if session:
        if session.expires_at and session.expires_at > datetime.utcnow():
            return SessionResponse.from_orm(session)
        else:
            # Session expired, create new one
            await db.delete(session)
            await db.commit()

    # Create new session
    expires_at = datetime.utcnow() + timedelta(
        minutes=settings.session_timeout_minutes
    )

    session = SessionModel(
        user_id=current_user_id,
        project_id=project_id,
        code_context={},
        chat_history=[],
        expires_at=expires_at,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SessionResponse.from_orm(session)


@router.put("/current/update", response_model=SessionResponse)
async def update_session(
    project_id: UUID,
    request: SessionUpdateRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current session (code context, chat history, execution errors).

    Args:
        project_id: Project ID
        request: Session update data
        current_user_id: Current user ID
        db: Database session

    Returns:
        Updated SessionResponse
    """
    # Get current session
    result = await db.execute(
        select(SessionModel).where(
            (SessionModel.user_id == current_user_id) &
            (SessionModel.project_id == project_id)
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Update fields
    if request.code_context is not None:
        session.code_context = request.code_context

    if request.chat_history is not None:
        # Convert ChatMessage objects to dict
        session.chat_history = [
            msg.dict() if hasattr(msg, 'dict') else msg
            for msg in request.chat_history
        ]

    if request.last_execution_error is not None:
        session.last_execution_error = request.last_execution_error

    # Update timestamp
    session.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(session)

    logger.info(f"✅ Session updated: {session.id}")

    return SessionResponse.from_orm(session)


@router.post("/current/add-chat-message")
async def add_chat_message(
    project_id: UUID,
    message: ChatMessage,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a message to chat history.

    Args:
        project_id: Project ID
        message: Chat message
        current_user_id: Current user ID
        db: Database session

    Returns:
        Updated SessionResponse
    """
    # Get current session
    result = await db.execute(
        select(SessionModel).where(
            (SessionModel.user_id == current_user_id) &
            (SessionModel.project_id == project_id)
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Add message
    message_dict = message.dict()
    if not isinstance(session.chat_history, list):
        session.chat_history = []

    session.chat_history.append(message_dict)

    # Limit history to last 100 messages
    if len(session.chat_history) > 100:
        session.chat_history = session.chat_history[-100:]

    session.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(session)

    return SessionResponse.from_orm(session)


@router.post("/current/set-execution-error")
async def set_execution_error(
    project_id: UUID,
    error: str,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Set last execution error for auto-fix suggestions.

    Args:
        project_id: Project ID
        error: Error message
        current_user_id: Current user ID
        db: Database session

    Returns:
        Updated SessionResponse
    """
    # Get current session
    result = await db.execute(
        select(SessionModel).where(
            (SessionModel.user_id == current_user_id) &
            (SessionModel.project_id == project_id)
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session.last_execution_error = error
    session.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(session)

    return SessionResponse.from_orm(session)


@router.post("/current/clear-execution-error")
async def clear_execution_error(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Clear last execution error.

    Args:
        project_id: Project ID
        current_user_id: Current user ID
        db: Database session

    Returns:
        Updated SessionResponse
    """
    result = await db.execute(
        select(SessionModel).where(
            (SessionModel.user_id == current_user_id) &
            (SessionModel.project_id == project_id)
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session.last_execution_error = None
    session.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(session)

    return SessionResponse.from_orm(session)


@router.delete("/current/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete current session.

    Args:
        project_id: Project ID
        current_user_id: Current user ID
        db: Database session
    """
    result = await db.execute(
        select(SessionModel).where(
            (SessionModel.user_id == current_user_id) &
            (SessionModel.project_id == project_id)
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    await db.delete(session)
    await db.commit()

    logger.info(f"✅ Session deleted: {session.id}")


@router.post("/cleanup-expired")
async def cleanup_expired_sessions(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete all expired sessions for current user.

    This can be called periodically by admin or scheduled task.

    Returns:
        Number of sessions deleted
    """
    # Get all expired sessions for this user
    result = await db.execute(
        select(SessionModel).where(
            (SessionModel.user_id == current_user_id) &
            (SessionModel.expires_at < datetime.utcnow())
        )
    )
    expired_sessions = result.scalars().all()

    # Delete them
    for session in expired_sessions:
        await db.delete(session)

    await db.commit()

    deleted_count = len(expired_sessions)
    logger.info(f"✅ Cleanup: {deleted_count} expired sessions deleted")

    return {
        "deleted_count": deleted_count,
        "message": f"Deleted {deleted_count} expired sessions"
    }
