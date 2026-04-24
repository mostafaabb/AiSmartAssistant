"""
WebSocket connection manager for real-time collaboration.
Handles live code editing, presence tracking, and message broadcasting.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Set, Dict, List, Optional
import json
import logging
from datetime import datetime
from uuid import UUID

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for a project.
    Handles:
    - User connections/disconnections
    - Code change broadcasts
    - Presence tracking (who's online)
    - Chat message delivery
    - Execution result streaming
    """

    def __init__(self):
        # Structure: {project_id: {user_id: {"websocket": ws, "cursor": pos, "user_name": str}}}
        self.active_connections: Dict[UUID, Dict[str, Dict]] = {}

    async def connect(self, project_id: UUID, user_id: str, websocket: WebSocket, user_name: str):
        """
        Register a new WebSocket connection.

        Args:
            project_id: Project being edited
            user_id: User connecting
            websocket: WebSocket connection
            user_name: Display name for presence
        """
        await websocket.accept()

        if project_id not in self.active_connections:
            self.active_connections[project_id] = {}

        self.active_connections[project_id][user_id] = {
            "websocket": websocket,
            "cursor": {"line": 0, "column": 0},
            "user_name": user_name,
            "connected_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"✅ User {user_name} ({user_id}) connected to project {project_id}"
        )

        # Notify others that user joined
        await self.broadcast_presence(project_id)

    def disconnect(self, project_id: UUID, user_id: str):
        """Remove a disconnected user."""
        if project_id in self.active_connections:
            if user_id in self.active_connections[project_id]:
                user_name = self.active_connections[project_id][user_id]["user_name"]
                del self.active_connections[project_id][user_id]
                logger.info(f"❌ User {user_name} disconnected from project {project_id}")

                # Clean up empty projects
                if not self.active_connections[project_id]:
                    del self.active_connections[project_id]

    async def broadcast(self, project_id: UUID, message: dict, exclude_user: Optional[str] = None):
        """
        Broadcast message to all connected users in a project.

        Args:
            project_id: Target project
            message: Message dict to send
            exclude_user: Optional user ID to exclude from broadcast
        """
        if project_id not in self.active_connections:
            return

        disconnected_users = []

        for user_id, conn_info in self.active_connections[project_id].items():
            if exclude_user and user_id == exclude_user:
                continue

            try:
                await conn_info["websocket"].send_json({
                    "type": message.get("type", "update"),
                    "data": message,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            except Exception as e:
                logger.error(f"Error broadcasting to {user_id}: {e}")
                disconnected_users.append(user_id)

        # Clean up failed connections
        for user_id in disconnected_users:
            self.disconnect(project_id, user_id)

    async def broadcast_presence(self, project_id: UUID):
        """
        Broadcast list of active users (presence awareness).

        Args:
            project_id: Target project
        """
        if project_id not in self.active_connections:
            return

        users = [
            {
                "user_id": user_id,
                "user_name": info["user_name"],
                "cursor": info.get("cursor", {"line": 0, "column": 0}),
                "connected_since": info["connected_at"],
            }
            for user_id, info in self.active_connections[project_id].items()
        ]

        await self.broadcast(project_id, {
            "type": "presence",
            "users": users,
            "count": len(users),
        })

    async def send_code_change(
        self,
        project_id: UUID,
        user_id: str,
        file_id: str,
        content: str,
        delta: Optional[dict] = None,
    ):
        """
        Broadcast code change to all other users.

        Args:
            project_id: Target project
            user_id: User making change
            file_id: File being edited
            content: Full file content
            delta: Optional delta/diff for optimization
        """
        message = {
            "type": "code_change",
            "file_id": file_id,
            "content": content,
            "delta": delta,
            "user_id": user_id,
        }

        await self.broadcast(project_id, message, exclude_user=user_id)

    async def send_cursor_position(
        self,
        project_id: UUID,
        user_id: str,
        line: int,
        column: int,
    ):
        """
        Broadcast user's cursor position for live collaboration.

        Args:
            project_id: Target project
            user_id: User moving cursor
            line: Line number
            column: Column number
        """
        if project_id in self.active_connections:
            if user_id in self.active_connections[project_id]:
                self.active_connections[project_id][user_id]["cursor"] = {
                    "line": line,
                    "column": column,
                }

        message = {
            "type": "cursor_move",
            "user_id": user_id,
            "cursor": {"line": line, "column": column},
        }

        await self.broadcast(project_id, message, exclude_user=user_id)

    async def send_chat_message(
        self,
        project_id: UUID,
        user_id: str,
        user_name: str,
        content: str,
    ):
        """
        Broadcast chat message to all users in project.

        Args:
            project_id: Target project
            user_id: User sending message
            user_name: User's display name
            content: Message content
        """
        message = {
            "type": "chat_message",
            "user_id": user_id,
            "user_name": user_name,
            "content": content,
        }

        await self.broadcast(project_id, message)

    async def send_execution_output(
        self,
        project_id: UUID,
        execution_id: str,
        output: str,
        error: Optional[str] = None,
        status: str = "running",
    ):
        """
        Stream code execution output to all users.

        Args:
            project_id: Target project
            execution_id: Execution ID
            output: Output text
            error: Error text (if any)
            status: Status (running, success, error, timeout)
        """
        message = {
            "type": "execution_output",
            "execution_id": execution_id,
            "output": output,
            "error": error,
            "status": status,
        }

        await self.broadcast(project_id, message)

    def get_connected_users(self, project_id: UUID) -> List[dict]:
        """Get list of users connected to a project."""
        if project_id not in self.active_connections:
            return []

        return [
            {
                "user_id": user_id,
                "user_name": info["user_name"],
            }
            for user_id, info in self.active_connections[project_id].items()
        ]

    def get_user_count(self, project_id: UUID) -> int:
        """Get number of connected users in a project."""
        return len(self.active_connections.get(project_id, {}))


# Global connection manager
manager = ConnectionManager()
