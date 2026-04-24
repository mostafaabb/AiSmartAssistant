"""
Chat/AI integration routes for NexusAI API.
Handles streaming and non-streaming AI responses with multiple providers.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List, Optional, AsyncGenerator
import logging
import json
import asyncio

from backend.app.core import get_db, get_current_user, settings
from backend.app.models import Session as SessionModel, Project
from backend.app.schemas import (
    ChatRequest,
    ChatMessage,
    ChatResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/projects", tags=["Chat & AI"])

# System prompt for better AI responses
SYSTEM_PROMPT = """You are NexusAI, an expert AI programming assistant. You help developers write, debug, and understand code.

Guidelines:
- Be concise but thorough
- Always provide working code examples when relevant
- Explain your reasoning step by step
- Use proper code formatting with language identifiers
- When fixing bugs, explain what was wrong and why the fix works
- Suggest best practices and optimizations when appropriate
- If you're unsure, say so and provide alternatives

Remember: You're helping a developer in an IDE, so prioritize practical, runnable code."""


async def call_ai_provider(
    messages: List[dict],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> AsyncGenerator[str, None]:
    """
    Call AI provider and stream responses.

    Supports multiple providers via LiteLLM.

    Args:
        messages: Chat messages
        model: Model name (uses default if None)
        temperature: Temperature parameter
        max_tokens: Max tokens to generate

    Yields:
        Streamed response content chunks
    """
    if not model:
        model = settings.default_model

    try:
        # Try using LiteLLM (unified interface)
        import litellm

        # Async streaming
        async for chunk in await asyncio.to_thread(
            litellm.acompletion,
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        ):
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        logger.error(f"AI provider error: {e}")
        yield f"\n\n⚠️ **Error**: {str(e)}"


@router.post("/{project_id}/chat/stream")
async def chat_stream(
    project_id: UUID,
    request: ChatRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream AI chat response (Server-Sent Events).

    Args:
        project_id: Project ID
        request: Chat request with messages
        current_user_id: Current user ID
        db: Database session

    Returns:
        StreamingResponse with SSE

    Raises:
        HTTPException 404: Project or session not found
        HTTPException 400: No API key configured
    """
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

    # Get or create session
    session_result = await db.execute(
        select(SessionModel).where(
            (SessionModel.user_id == current_user_id) &
            (SessionModel.project_id == project_id)
        )
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if not settings.openrouter_api_key and not settings.default_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI API key not configured"
        )

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events."""
        try:
            # Add system prompt
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *[msg.dict() for msg in request.messages]
            ]

            # Get response from AI
            full_response = ""

            async for chunk in call_ai_provider(
                messages=messages,
                model=request.model,
            ):
                full_response += chunk
                # Send as SSE
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            # Save to session history
            session.chat_history.append({
                "role": "user",
                "content": request.messages[-1].content if request.messages else ""
            })
            session.chat_history.append({
                "role": "assistant",
                "content": full_response
            })

            # Limit history to 100 messages
            if len(session.chat_history) > 100:
                session.chat_history = session.chat_history[-100:]

            await db.commit()

            logger.info(f"✅ Chat completed: {len(full_response)} chars")

        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.post("/{project_id}/chat", response_model=ChatResponse)
async def chat_non_streaming(
    project_id: UUID,
    request: ChatRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Non-streaming chat API (waits for full response).

    Useful for simple requests that don't need real-time updates.

    Args:
        project_id: Project ID
        request: Chat request
        current_user_id: Current user ID
        db: Database session

    Returns:
        ChatResponse with full response text
    """
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

    # Get session
    session_result = await db.execute(
        select(SessionModel).where(
            (SessionModel.user_id == current_user_id) &
            (SessionModel.project_id == project_id)
        )
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    try:
        # Create messages list
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *[msg.dict() for msg in request.messages]
        ]

        # Collect full response
        full_response = ""
        async for chunk in call_ai_provider(
            messages=messages,
            model=request.model,
        ):
            full_response += chunk

        # Save to session
        session.chat_history.append({
            "role": "user",
            "content": request.messages[-1].content if request.messages else ""
        })
        session.chat_history.append({
            "role": "assistant",
            "content": full_response
        })

        await db.commit()

        logger.info(f"✅ Chat (non-streaming): {len(full_response)} chars")

        return ChatResponse(content=full_response)

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


@router.get("/{project_id}/chat/history")
async def get_chat_history(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get chat history for a session.

    Args:
        project_id: Project ID
        current_user_id: Current user ID
        db: Database session

    Returns:
        List of chat messages
    """
    session_result = await db.execute(
        select(SessionModel).where(
            (SessionModel.user_id == current_user_id) &
            (SessionModel.project_id == project_id)
        )
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return session.chat_history


@router.delete("/{project_id}/chat/clear")
async def clear_chat_history(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Clear chat history for a session.

    Args:
        project_id: Project ID
        current_user_id: Current user ID
        db: Database session

    Returns:
        Success message
    """
    session_result = await db.execute(
        select(SessionModel).where(
            (SessionModel.user_id == current_user_id) &
            (SessionModel.project_id == project_id)
        )
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session.chat_history = []
    await db.commit()

    logger.info(f"✅ Chat history cleared: {project_id}")

    return {"message": "Chat history cleared"}


@router.get("/models")
async def list_available_models():
    """
    List available AI models.

    Returns:
        List of available models
    """
    return {
        "default": settings.default_model,
        "available_models": [
            {
                "name": "Google Gemini 2.0 Flash",
                "id": "google/gemini-2.0-flash-exp:free",
                "type": "fast",
                "cost": "free"
            },
            {
                "name": "OpenAI GPT-3.5 Turbo",
                "id": "openai/gpt-3.5-turbo",
                "type": "balanced",
                "cost": "paid"
            },
            {
                "name": "OpenAI GPT-4",
                "id": "openai/gpt-4",
                "type": "powerful",
                "cost": "paid"
            },
            {
                "name": "Anthropic Claude 3 Opus",
                "id": "anthropic/claude-3-opus",
                "type": "powerful",
                "cost": "paid"
            },
            {
                "name": "Meta Llama 3.3 70B",
                "id": "meta-llama/llama-3.3-70b-instruct:free",
                "type": "powerful",
                "cost": "free"
            },
            {
                "name": "DeepSeek R1",
                "id": "deepseek/deepseek-r1-0528:free",
                "type": "reasoning",
                "cost": "free"
            },
        ]
    }
