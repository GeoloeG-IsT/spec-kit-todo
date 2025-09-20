"""
Real-time streaming API routes using Server-Sent Events (SSE).

Provides real-time updates for TODO changes, allowing clients to
receive live notifications when TODOs are created, updated, or deleted.
Uses SSE which is compatible with Cloud Run deployments.
"""

import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
import structlog

from ...application.services.realtime_service import RealtimeService
from ...api.middleware.auth import require_auth

logger = structlog.get_logger(__name__)

router = APIRouter()

# Global realtime service instance
realtime_service = RealtimeService()


@router.get("/events", tags=["Real-time"])
async def stream_todo_events(
    request: Request,
    user_context: dict = Depends(require_auth)
):
    """
    Stream real-time TODO events using Server-Sent Events (SSE).

    Establishes a persistent connection to receive live updates when:
    - TODOs are created, updated, or deleted
    - Bulk operations are performed
    - Other users make changes (for shared TODOs in the future)

    The connection automatically handles:
    - Heartbeat messages to keep connection alive
    - Reconnection after network issues
    - Proper cleanup when client disconnects

    Returns:
        SSE stream with real-time events
    """
    # Create a queue for this connection
    connection_queue = asyncio.Queue()

    # Connection metadata
    metadata = {
        "user_agent": request.headers.get("user-agent"),
        "ip_address": request.client.host if request.client else None,
        "connected_at": asyncio.get_event_loop().time()
    }

    # Add connection based on user type
    if user_context["type"] == "user":
        user_id = user_context["user_id"]
        await realtime_service.add_user_connection(user_id, connection_queue, metadata)
        logger.info("User connected to SSE stream", user_id=user_id)
    else:  # guest
        session_id = user_context["session_id"]
        await realtime_service.add_session_connection(session_id, connection_queue, metadata)
        logger.info("Guest session connected to SSE stream", session_id=session_id)

    # Create the event stream
    async def event_stream() -> AsyncGenerator[str, None]:
        """Generate SSE events for this connection."""
        try:
            async for message in realtime_service.create_event_stream(connection_queue):
                yield message
        except asyncio.CancelledError:
            logger.info("SSE stream cancelled by client")
        except Exception as e:
            logger.error("Error in SSE stream", error=str(e))
        finally:
            # Cleanup is handled by the realtime service
            pass

    # Return streaming response with SSE headers
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get("/connection-stats", tags=["Real-time"])
async def get_connection_stats():
    """
    Get statistics about active SSE connections.

    This endpoint is useful for monitoring and debugging
    real-time functionality.

    Returns:
        Connection statistics including active users and sessions
    """
    stats = realtime_service.get_connection_stats()
    logger.info("Connection stats requested", stats=stats)
    return stats


@router.post("/test-notification", tags=["Real-time"])
async def send_test_notification(
    user_context: dict = Depends(require_auth)
):
    """
    Send a test notification to verify real-time functionality.

    This endpoint is useful for testing SSE connections and
    debugging real-time features during development.

    Returns:
        Number of connections the test message was sent to
    """
    test_data = {
        "message": "This is a test notification",
        "timestamp": "2024-01-01T00:00:00Z",
        "test": True
    }

    # Send test notification based on user type
    if user_context["type"] == "user":
        user_id = user_context["user_id"]
        sent_count = await realtime_service.broadcast_to_user(user_id, "test_notification", test_data)
        logger.info("Test notification sent to user", user_id=user_id, sent_count=sent_count)
    else:  # guest
        session_id = user_context["session_id"]
        sent_count = await realtime_service.broadcast_to_session(session_id, "test_notification", test_data)
        logger.info("Test notification sent to session", session_id=session_id, sent_count=sent_count)

    return {
        "message": "Test notification sent",
        "connections_notified": sent_count,
        "user_type": user_context["type"]
    }


@router.get("/stream-info", tags=["Real-time"])
async def get_stream_info(
    user_context: dict = Depends(require_auth)
):
    """
    Get information about the real-time streaming setup.

    Provides clients with details about the SSE connection,
    supported events, and configuration.

    Returns:
        Streaming configuration and capabilities
    """
    return {
        "protocol": "Server-Sent Events (SSE)",
        "endpoint": "/api/todos/events",
        "supported_events": [
            "connected",
            "heartbeat",
            "todo_created",
            "todo_updated",
            "todo_deleted",
            "todos_bulk_updated",
            "test_notification"
        ],
        "features": {
            "automatic_reconnection": True,
            "heartbeat_interval_seconds": 30,
            "connection_timeout": "No timeout (persistent)",
            "cloud_run_compatible": True
        },
        "client_requirements": {
            "headers": {
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            },
            "authentication": "Bearer token or session cookie required"
        },
        "event_format": {
            "example": "event: todo_created\\ndata: {\"todo\": {...}, \"timestamp\": \"...\"}\\n\\n",
            "content_type": "application/json (in data field)"
        }
    }