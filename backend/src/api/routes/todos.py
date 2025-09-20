"""
TODO API routes for managing TODO items.

Handles CRUD operations, bulk updates, and reordering for TODO items.
Supports both authenticated users and guest sessions with proper
ownership verification and real-time notifications.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ...infrastructure.database import get_db_session
from ...application.services.todo_service import TodoService
from ...application.services.realtime_service import RealtimeService
from ...api.middleware.auth import require_auth
from ...domain.schemas import (
    TodoItemCreate, TodoItemUpdate, TodoItemResponse, TodoItemListResponse,
    TodoItemBulkUpdate, TodoItemReorder, BulkUpdateResponse, ErrorResponse
)

logger = structlog.get_logger(__name__)

router = APIRouter()

# Global realtime service instance
realtime_service = RealtimeService()


@router.post("/", response_model=TodoItemResponse, status_code=201, tags=["TODO Management"])
async def create_todo(
    todo_data: TodoItemCreate,
    user_context: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Create a new TODO item.

    Works for both authenticated users and guest sessions.

    Args:
        todo_data: TODO creation data

    Returns:
        Created TODO item
    """
    todo_service = TodoService(session)

    # Create TODO based on user type
    if user_context["type"] == "user":
        user_id = UUID(user_context["user_id"])
        todo = await todo_service.create_todo_for_user(user_id, todo_data)
        owner_id = str(user_id)
        session_id = None
    else:  # guest
        session_id = user_context["session_id"]
        todo = await todo_service.create_todo_for_session(session_id, todo_data)
        owner_id = None

    # Convert to response format
    todo_response = todo_service.to_response(todo)

    # Send real-time notification
    await realtime_service.notify_todo_created(
        todo_response.model_dump(),
        user_id=owner_id,
        session_id=session_id
    )

    logger.info("TODO created", todo_id=str(todo.id), owner_type=user_context["type"])
    return todo_response


@router.get("/", response_model=TodoItemListResponse, tags=["TODO Management"])
async def get_todos(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    priority: Optional[str] = Query(None, pattern="^(low|medium|high)$", description="Filter by priority"),
    order_by: Optional[str] = Query(None, pattern="^(created_at|updated_at|title|priority|order_index)$", description="Order by field"),
    order_direction: Optional[str] = Query("asc", pattern="^(asc|desc)$", description="Order direction"),
    user_context: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get TODO items with pagination.

    Returns TODOs for the current user or guest session.

    Args:
        limit: Maximum number of items to return (1-1000)
        offset: Number of items to skip for pagination

    Returns:
        Paginated list of TODO items
    """
    todo_service = TodoService(session)

    # Get TODOs based on user type
    if user_context["type"] == "user":
        user_id = UUID(user_context["user_id"])
        todos = await todo_service.get_todos_for_user(
            user_id, limit, offset, completed, priority
        )
    else:  # guest
        session_id = user_context["session_id"]
        todos = await todo_service.get_todos_for_session(
            session_id, limit, offset, completed, priority
        )

    return todos


@router.get("/{todo_id}", response_model=TodoItemResponse, tags=["TODO Management"])
async def get_todo(
    todo_id: UUID,
    user_context: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get a specific TODO item by ID.

    Verifies ownership before returning the TODO.

    Args:
        todo_id: TODO item UUID

    Returns:
        TODO item details
    """
    todo_service = TodoService(session)

    # Get TODO with ownership verification
    todo = await todo_service.get_todo_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="TODO not found")

    # Verify ownership
    if user_context["type"] == "user":
        if todo.user_id != UUID(user_context["user_id"]):
            raise HTTPException(status_code=404, detail="TODO not found")
    else:  # guest
        if todo.session_id != user_context["session_id"]:
            raise HTTPException(status_code=404, detail="TODO not found")

    return todo_service.to_response(todo)


@router.put("/{todo_id}", response_model=TodoItemResponse, tags=["TODO Management"])
async def update_todo(
    todo_id: UUID,
    todo_update: TodoItemUpdate,
    user_context: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Update a TODO item.

    Verifies ownership before updating.

    Args:
        todo_id: TODO item UUID
        todo_update: Update data

    Returns:
        Updated TODO item
    """
    todo_service = TodoService(session)

    # Prepare ownership parameters
    if user_context["type"] == "user":
        user_id = UUID(user_context["user_id"])
        session_id = None
        owner_id = str(user_id)
    else:  # guest
        user_id = None
        session_id = user_context["session_id"]
        owner_id = None

    # Update TODO with ownership verification
    todo = await todo_service.update_todo(todo_id, todo_update, user_id, session_id)
    if not todo:
        raise HTTPException(status_code=404, detail="TODO not found")

    # Convert to response format
    todo_response = todo_service.to_response(todo)

    # Send real-time notification
    await realtime_service.notify_todo_updated(
        todo_response.model_dump(),
        user_id=owner_id,
        session_id=session_id
    )

    logger.info("TODO updated", todo_id=str(todo_id), owner_type=user_context["type"])
    return todo_response


@router.delete("/{todo_id}", status_code=204, tags=["TODO Management"])
async def delete_todo(
    todo_id: UUID,
    user_context: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Delete a TODO item (soft delete).

    Verifies ownership before deletion.

    Args:
        todo_id: TODO item UUID

    Returns:
        No content (204) on successful deletion
    """
    todo_service = TodoService(session)

    # Prepare ownership parameters
    if user_context["type"] == "user":
        user_id = UUID(user_context["user_id"])
        session_id = None
        owner_id = str(user_id)
    else:  # guest
        user_id = None
        session_id = user_context["session_id"]
        owner_id = None

    # Delete TODO with ownership verification
    deleted = await todo_service.delete_todo(todo_id, user_id, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="TODO not found")

    # Send real-time notification
    await realtime_service.notify_todo_deleted(
        str(todo_id),
        user_id=owner_id,
        session_id=session_id
    )

    logger.info("TODO deleted", todo_id=str(todo_id), owner_type=user_context["type"])


@router.post("/bulk-update", response_model=BulkUpdateResponse, tags=["Bulk Operations"])
async def bulk_update_todos(
    bulk_update: TodoItemBulkUpdate,
    user_context: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Bulk update multiple TODO items.

    Updates completion status and/or priority for multiple TODOs.
    Verifies ownership of all TODOs before updating.

    Args:
        bulk_update: Bulk update data with TODO IDs and changes

    Returns:
        Number of TODOs updated
    """
    todo_service = TodoService(session)

    # Prepare ownership parameters
    if user_context["type"] == "user":
        user_id = UUID(user_context["user_id"])
        session_id = None
        owner_id = str(user_id)
    else:  # guest
        user_id = None
        session_id = user_context["session_id"]
        owner_id = None

    # Perform bulk update with ownership verification
    result = await todo_service.bulk_update_todos(bulk_update, user_id, session_id)

    # If any TODOs were updated, send real-time notification
    if result.updated_count > 0:
        # Get updated TODOs for notification
        updated_todos = []
        for todo_id in bulk_update.todo_ids:
            todo = await todo_service.get_todo_by_id(todo_id)
            if todo:
                updated_todos.append(todo_service.to_response(todo).model_dump())

        await realtime_service.notify_bulk_update(
            updated_todos,
            user_id=owner_id,
            session_id=session_id
        )

    logger.info("Bulk TODO update completed",
               updated_count=result.updated_count, owner_type=user_context["type"])
    return result


@router.post("/reorder", response_model=BulkUpdateResponse, tags=["Bulk Operations"])
async def reorder_todos(
    reorder_data: TodoItemReorder,
    user_context: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Reorder TODO items by updating their order indices.

    Allows custom ordering of TODOs. Verifies ownership
    of all TODOs before reordering.

    Args:
        reorder_data: Reorder data with TODO IDs and new order indices

    Returns:
        Number of TODOs reordered
    """
    todo_service = TodoService(session)

    # Prepare ownership parameters
    if user_context["type"] == "user":
        user_id = UUID(user_context["user_id"])
        session_id = None
        owner_id = str(user_id)
    else:  # guest
        user_id = None
        session_id = user_context["session_id"]
        owner_id = None

    # Perform reorder with ownership verification
    result = await todo_service.reorder_todos(reorder_data, user_id, session_id)

    # If any TODOs were reordered, send real-time notification
    if result.updated_count > 0:
        # Get reordered TODOs for notification
        reordered_todos = []
        for todo_order in reorder_data.todo_orders:
            todo = await todo_service.get_todo_by_id(todo_order.todo_id)
            if todo:
                reordered_todos.append(todo_service.to_response(todo).model_dump())

        await realtime_service.notify_bulk_update(
            reordered_todos,
            user_id=owner_id,
            session_id=session_id
        )

    logger.info("TODO reorder completed",
               updated_count=result.updated_count, owner_type=user_context["type"])
    return result