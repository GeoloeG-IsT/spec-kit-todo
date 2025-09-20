"""
Real-time service for managing Server-Sent Events (SSE) connections.

Handles real-time notifications for TODO updates, user presence,
and other live updates using SSE which is compatible with Cloud Run.
"""

import asyncio
import json
from typing import Dict, Set, Optional, Any, AsyncGenerator
from datetime import datetime
from uuid import UUID

import structlog

logger = structlog.get_logger(__name__)


class RealtimeService:
    """Service for real-time communication using Server-Sent Events."""

    def __init__(self):
        # Store active connections by user/session
        self._user_connections: Dict[str, Set[asyncio.Queue]] = {}
        self._session_connections: Dict[str, Set[asyncio.Queue]] = {}
        self._connection_metadata: Dict[asyncio.Queue, Dict[str, Any]] = {}

    async def add_user_connection(self, user_id: str, connection_queue: asyncio.Queue,
                                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a new SSE connection for an authenticated user.

        Args:
            user_id: User's ID (UUID as string)
            connection_queue: Queue for sending messages to this connection
            metadata: Optional connection metadata
        """
        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()

        self._user_connections[user_id].add(connection_queue)
        self._connection_metadata[connection_queue] = metadata or {}

        logger.info("User SSE connection added", user_id=user_id,
                   total_connections=len(self._user_connections[user_id]))

    async def add_session_connection(self, session_id: str, connection_queue: asyncio.Queue,
                                    metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a new SSE connection for a guest session.

        Args:
            session_id: Guest session ID
            connection_queue: Queue for sending messages to this connection
            metadata: Optional connection metadata
        """
        if session_id not in self._session_connections:
            self._session_connections[session_id] = set()

        self._session_connections[session_id].add(connection_queue)
        self._connection_metadata[connection_queue] = metadata or {}

        logger.info("Session SSE connection added", session_id=session_id,
                   total_connections=len(self._session_connections[session_id]))

    async def remove_connection(self, connection_queue: asyncio.Queue) -> None:
        """
        Remove an SSE connection.

        Args:
            connection_queue: Connection queue to remove
        """
        # Remove from user connections
        for user_id, connections in self._user_connections.items():
            if connection_queue in connections:
                connections.remove(connection_queue)
                if not connections:
                    del self._user_connections[user_id]
                logger.info("User SSE connection removed", user_id=user_id)
                break

        # Remove from session connections
        for session_id, connections in self._session_connections.items():
            if connection_queue in connections:
                connections.remove(connection_queue)
                if not connections:
                    del self._session_connections[session_id]
                logger.info("Session SSE connection removed", session_id=session_id)
                break

        # Remove metadata
        if connection_queue in self._connection_metadata:
            del self._connection_metadata[connection_queue]

    async def broadcast_to_user(self, user_id: str, event_type: str, data: Dict[str, Any]) -> int:
        """
        Broadcast a message to all connections for a specific user.

        Args:
            user_id: Target user ID
            event_type: Type of event (e.g., 'todo_updated', 'todo_created')
            data: Event data

        Returns:
            Number of connections the message was sent to
        """
        if user_id not in self._user_connections:
            return 0

        message = self._format_sse_message(event_type, data)
        connections = list(self._user_connections[user_id])  # Copy to avoid modification during iteration
        sent_count = 0

        for connection_queue in connections:
            try:
                await connection_queue.put(message)
                sent_count += 1
            except Exception as e:
                logger.error("Failed to send message to user connection",
                           user_id=user_id, error=str(e))
                # Remove broken connection
                await self.remove_connection(connection_queue)

        logger.info("Message broadcast to user", user_id=user_id,
                   event_type=event_type, sent_count=sent_count)
        return sent_count

    async def broadcast_to_session(self, session_id: str, event_type: str, data: Dict[str, Any]) -> int:
        """
        Broadcast a message to all connections for a specific session.

        Args:
            session_id: Target session ID
            event_type: Type of event
            data: Event data

        Returns:
            Number of connections the message was sent to
        """
        if session_id not in self._session_connections:
            return 0

        message = self._format_sse_message(event_type, data)
        connections = list(self._session_connections[session_id])  # Copy to avoid modification during iteration
        sent_count = 0

        for connection_queue in connections:
            try:
                await connection_queue.put(message)
                sent_count += 1
            except Exception as e:
                logger.error("Failed to send message to session connection",
                           session_id=session_id, error=str(e))
                # Remove broken connection
                await self.remove_connection(connection_queue)

        logger.info("Message broadcast to session", session_id=session_id,
                   event_type=event_type, sent_count=sent_count)
        return sent_count

    async def notify_todo_created(self, todo_data: Dict[str, Any], user_id: Optional[str] = None,
                                 session_id: Optional[str] = None) -> int:
        """
        Notify about a new TODO being created.

        Args:
            todo_data: TODO data
            user_id: User ID (for authenticated users)
            session_id: Session ID (for guest users)

        Returns:
            Number of connections notified
        """
        event_data = {
            "todo": todo_data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        if user_id:
            return await self.broadcast_to_user(user_id, "todo_created", event_data)
        elif session_id:
            return await self.broadcast_to_session(session_id, "todo_created", event_data)
        else:
            return 0

    async def notify_todo_updated(self, todo_data: Dict[str, Any], user_id: Optional[str] = None,
                                 session_id: Optional[str] = None) -> int:
        """
        Notify about a TODO being updated.

        Args:
            todo_data: Updated TODO data
            user_id: User ID (for authenticated users)
            session_id: Session ID (for guest users)

        Returns:
            Number of connections notified
        """
        event_data = {
            "todo": todo_data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        if user_id:
            return await self.broadcast_to_user(user_id, "todo_updated", event_data)
        elif session_id:
            return await self.broadcast_to_session(session_id, "todo_updated", event_data)
        else:
            return 0

    async def notify_todo_deleted(self, todo_id: str, user_id: Optional[str] = None,
                                 session_id: Optional[str] = None) -> int:
        """
        Notify about a TODO being deleted.

        Args:
            todo_id: ID of deleted TODO
            user_id: User ID (for authenticated users)
            session_id: Session ID (for guest users)

        Returns:
            Number of connections notified
        """
        event_data = {
            "todo_id": todo_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        if user_id:
            return await self.broadcast_to_user(user_id, "todo_deleted", event_data)
        elif session_id:
            return await self.broadcast_to_session(session_id, "todo_deleted", event_data)
        else:
            return 0

    async def notify_bulk_update(self, updated_todos: list, user_id: Optional[str] = None,
                                session_id: Optional[str] = None) -> int:
        """
        Notify about bulk TODO updates.

        Args:
            updated_todos: List of updated TODO data
            user_id: User ID (for authenticated users)
            session_id: Session ID (for guest users)

        Returns:
            Number of connections notified
        """
        event_data = {
            "todos": updated_todos,
            "count": len(updated_todos),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        if user_id:
            return await self.broadcast_to_user(user_id, "todos_bulk_updated", event_data)
        elif session_id:
            return await self.broadcast_to_session(session_id, "todos_bulk_updated", event_data)
        else:
            return 0

    async def create_event_stream(self, connection_queue: asyncio.Queue) -> AsyncGenerator[str, None]:
        """
        Create an SSE event stream for a connection.

        Args:
            connection_queue: Queue to receive messages from

        Yields:
            SSE-formatted messages
        """
        try:
            # Send initial connection message
            initial_message = self._format_sse_message("connected", {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": "Real-time connection established"
            })
            yield initial_message

            # Send heartbeat and messages
            while True:
                try:
                    # Wait for message with timeout for heartbeat
                    message = await asyncio.wait_for(connection_queue.get(), timeout=30.0)
                    yield message
                except asyncio.TimeoutError:
                    # Send heartbeat
                    heartbeat = self._format_sse_message("heartbeat", {
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
                    yield heartbeat
                except Exception as e:
                    logger.error("Error in event stream", error=str(e))
                    break

        except Exception as e:
            logger.error("Event stream error", error=str(e))
        finally:
            # Clean up connection
            await self.remove_connection(connection_queue)

    def _format_sse_message(self, event_type: str, data: Dict[str, Any]) -> str:
        """
        Format a message for Server-Sent Events.

        Args:
            event_type: Type of event
            data: Event data

        Returns:
            SSE-formatted message string
        """
        json_data = json.dumps(data, default=str)
        return f"event: {event_type}\ndata: {json_data}\n\n"

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about active connections.

        Returns:
            Dictionary with connection statistics
        """
        total_user_connections = sum(len(connections) for connections in self._user_connections.values())
        total_session_connections = sum(len(connections) for connections in self._session_connections.values())

        return {
            "total_connections": total_user_connections + total_session_connections,
            "user_connections": total_user_connections,
            "session_connections": total_session_connections,
            "active_users": len(self._user_connections),
            "active_sessions": len(self._session_connections)
        }