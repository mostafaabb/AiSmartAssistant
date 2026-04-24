"""
WebSocket endpoint for real-time collaboration.
Handles live code editing, presence tracking, and chat.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Depends
from uuid import UUID
import json
import logging
from typing import Optional

from backend.app.services.websocket_manager import manager
from backend.app.core import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/ws/project/{project_id}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: UUID,
    user_id: str,
    token: Optional[str] = None,
):
    """
    WebSocket endpoint for real-time collaboration.

    Handles:
    - Code change synchronization
    - Live cursor positions
    - Chat messages
    - Execution result streaming
    - Presence tracking

    Message Types:
    - code_change {file_id, content, delta}
    - cursor_move {line, column}
    - chat_message {content}
    - execution_result {execution_id, output, status}
    - ping (keep-alive)

    Example connection:
    ws://localhost:8000/ws/project/{project_id}/{user_id}?token=jwt_token
    """
    try:
        # Verify JWT token from query parameter
        if token:
            try:
                payload = verify_token(token)
                verified_user = payload.get("sub")
                if verified_user != user_id:
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    logger.warning(f"Token user {verified_user} != requested user {user_id}")
                    return
            except Exception as e:
                logger.error(f"Token verification failed: {e}")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
        else:
            logger.warning(f"WebSocket connection without token from {user_id}")

        # Connect user
        user_name = f"User_{user_id[:8]}"  # Simple name, can be enhanced
        await manager.connect(project_id, user_id, websocket, user_name)

        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": f"Welcome {user_name}!",
            "project_id": str(project_id),
            "user_id": user_id,
        })

        # Listen for messages
        while True:
            data = await websocket.receive_json()

            try:
                message_type = data.get("type")
                logger.debug(f"WebSocket message from {user_id}: {message_type}")

                # Handle different message types
                if message_type == "code_change":
                    # Code change from user's editor
                    await manager.send_code_change(
                        project_id=project_id,
                        user_id=user_id,
                        file_id=data.get("file_id"),
                        content=data.get("content"),
                        delta=data.get("delta"),
                    )

                elif message_type == "cursor_move":
                    # Cursor position update (for live collaboration)
                    await manager.send_cursor_position(
                        project_id=project_id,
                        user_id=user_id,
                        line=data.get("line", 0),
                        column=data.get("column", 0),
                    )

                    # Also update locally
                    if project_id in manager.active_connections:
                        if user_id in manager.active_connections[project_id]:
                            manager.active_connections[project_id][user_id]["cursor"] = {
                                "line": data.get("line", 0),
                                "column": data.get("column", 0),
                            }

                elif message_type == "chat_message":
                    # Chat message from user
                    await manager.send_chat_message(
                        project_id=project_id,
                        user_id=user_id,
                        user_name=user_name,
                        content=data.get("content", ""),
                    )

                elif message_type == "execution_result":
                    # Code execution result streaming
                    await manager.send_execution_output(
                        project_id=project_id,
                        execution_id=data.get("execution_id"),
                        output=data.get("output", ""),
                        error=data.get("error"),
                        status=data.get("status", "running"),
                    )

                elif message_type == "ping":
                    # Keep-alive ping
                    await websocket.send_json({"type": "pong"})

                else:
                    logger.warning(f"Unknown message type: {message_type}")

            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format",
                })
            except Exception as e:
                logger.error(f"Error handling message: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error: {str(e)}",
                })

    except WebSocketDisconnect:
        manager.disconnect(project_id, user_id)
        logger.info(f"⚠️  WebSocket disconnected: user {user_id}")

        # Notify others that user left
        await manager.broadcast_presence(project_id)

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(project_id, user_id)


@router.get("/ws/project/{project_id}/users")
async def get_project_users(project_id: UUID):
    """
    Get list of users currently connected to a project.

    Returns:
        List of connected users with their info
    """
    users = manager.get_connected_users(project_id)
    return {
        "project_id": str(project_id),
        "users": users,
        "count": len(users),
    }


@router.get("/ws/project/{project_id}/presence")
async def get_project_presence(project_id: UUID):
    """
    Get presence information for a project.

    Returns:
        Number of active users
    """
    count = manager.get_user_count(project_id)
    return {
        "project_id": str(project_id),
        "active_users": count,
    }
