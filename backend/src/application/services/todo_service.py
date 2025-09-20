"""
TODO service for managing TODO item operations.

Handles CRUD operations, bulk updates, reordering, and session-to-user migration
for TODO items. Supports both authenticated users and guest sessions.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.exc import IntegrityError
import structlog

from ...domain.models.todo_item import TodoItem, TodoPriority
from ...domain.schemas import (
    TodoItemCreate, TodoItemUpdate, TodoItemResponse,
    TodoItemListResponse, TodoItemBulkUpdate, TodoItemReorder,
    BulkUpdateResponse
)

logger = structlog.get_logger(__name__)


class TodoService:
    """Service for TODO item management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_todo_for_user(self, user_id: UUID, todo_data: TodoItemCreate) -> TodoItem:
        """
        Create a new TODO for a registered user.

        Args:
            user_id: User's UUID
            todo_data: TODO creation data

        Returns:
            Created TODO item
        """
        # Get next order index for user
        order_index = await self._get_next_order_index_for_user(user_id)

        todo = TodoItem.create_for_user(
            user_id=user_id,
            title=todo_data.title,
            description=todo_data.description,
            priority=todo_data.priority
        )
        todo.order_index = order_index

        self.session.add(todo)
        await self.session.commit()
        await self.session.refresh(todo)

        logger.info("TODO created for user", todo_id=str(todo.id), user_id=str(user_id))
        return todo

    async def create_todo_for_session(self, session_id: str, todo_data: TodoItemCreate) -> TodoItem:
        """
        Create a new TODO for a guest session.

        Args:
            session_id: Guest session ID
            todo_data: TODO creation data

        Returns:
            Created TODO item
        """
        # Get next order index for session
        order_index = await self._get_next_order_index_for_session(session_id)

        todo = TodoItem.create_for_session(
            session_id=session_id,
            title=todo_data.title,
            description=todo_data.description,
            priority=todo_data.priority
        )
        todo.order_index = order_index

        self.session.add(todo)
        await self.session.commit()
        await self.session.refresh(todo)

        logger.info("TODO created for session", todo_id=str(todo.id), session_id=session_id)
        return todo

    async def get_todo_by_id(self, todo_id: UUID) -> Optional[TodoItem]:
        """Get TODO by ID."""
        result = await self.session.execute(
            select(TodoItem).where(
                TodoItem.id == todo_id,
                TodoItem.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_todos_for_user(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
        completed: Optional[bool] = None,
        priority: Optional[str] = None
    ) -> TodoItemListResponse:
        """
        Get TODOs for a registered user with pagination.

        Args:
            user_id: User's UUID
            limit: Maximum number of items to return
            offset: Number of items to skip

        Returns:
            Paginated list of TODOs
        """
        # Build where conditions
        where_conditions = [
            TodoItem.user_id == user_id,
            TodoItem.deleted_at.is_(None)
        ]

        # Add filtering conditions
        if completed is not None:
            where_conditions.append(TodoItem.completed == completed)
        if priority is not None:
            where_conditions.append(TodoItem.priority == priority)

        # Get total count with filters
        count_result = await self.session.execute(
            select(func.count(TodoItem.id)).where(*where_conditions)
        )
        total = count_result.scalar() or 0

        # Get TODOs ordered by order_index, then by created_at
        result = await self.session.execute(
            select(TodoItem)
            .where(*where_conditions)
            .order_by(TodoItem.order_index, TodoItem.created_at)
            .limit(limit)
            .offset(offset)
        )
        todos = list(result.scalars().all())

        return TodoItemListResponse(
            items=[self.to_response(todo) for todo in todos],
            total=total,
            limit=limit,
            offset=offset
        )

    async def get_todos_for_session(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
        completed: Optional[bool] = None,
        priority: Optional[str] = None
    ) -> TodoItemListResponse:
        """
        Get TODOs for a guest session with pagination.

        Args:
            session_id: Guest session ID
            limit: Maximum number of items to return
            offset: Number of items to skip

        Returns:
            Paginated list of TODOs
        """
        # Build where conditions
        where_conditions = [
            TodoItem.session_id == session_id,
            TodoItem.deleted_at.is_(None)
        ]

        # Add filtering conditions
        if completed is not None:
            where_conditions.append(TodoItem.completed == completed)
        if priority is not None:
            where_conditions.append(TodoItem.priority == priority)

        # Get total count with filters
        count_result = await self.session.execute(
            select(func.count(TodoItem.id)).where(*where_conditions)
        )
        total = count_result.scalar() or 0

        # Get TODOs ordered by order_index, then by created_at
        result = await self.session.execute(
            select(TodoItem)
            .where(*where_conditions)
            .order_by(TodoItem.order_index, TodoItem.created_at)
            .limit(limit)
            .offset(offset)
        )
        todos = list(result.scalars().all())

        return TodoItemListResponse(
            items=[self.to_response(todo) for todo in todos],
            total=total,
            limit=limit,
            offset=offset
        )

    async def update_todo(self, todo_id: UUID, todo_update: TodoItemUpdate,
                         user_id: Optional[UUID] = None, session_id: Optional[str] = None) -> Optional[TodoItem]:
        """
        Update a TODO item.

        Args:
            todo_id: TODO's UUID
            todo_update: Update data
            user_id: User ID (for ownership verification)
            session_id: Session ID (for ownership verification)

        Returns:
            Updated TODO or None if not found/not owned
        """
        # Build ownership filter
        ownership_filter = self._build_ownership_filter(user_id, session_id)

        # Get the TODO with ownership verification
        result = await self.session.execute(
            select(TodoItem).where(
                TodoItem.id == todo_id,
                TodoItem.deleted_at.is_(None),
                ownership_filter
            )
        )
        todo = result.scalar_one_or_none()

        if not todo:
            return None

        # Update fields
        if todo_update.title is not None:
            todo.title = todo_update.title
        if todo_update.description is not None:
            todo.description = todo_update.description
        if todo_update.priority is not None:
            todo.priority = todo_update.priority
        if todo_update.completed is not None:
            if todo_update.completed and not todo.completed:
                todo.mark_completed()
            elif not todo_update.completed and todo.completed:
                todo.mark_pending()
        if todo_update.order_index is not None:
            todo.set_order_index(todo_update.order_index)

        todo.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(todo)

        logger.info("TODO updated", todo_id=str(todo_id))
        return todo

    async def delete_todo(self, todo_id: UUID, user_id: Optional[UUID] = None,
                         session_id: Optional[str] = None) -> bool:
        """
        Soft delete a TODO item.

        Args:
            todo_id: TODO's UUID
            user_id: User ID (for ownership verification)
            session_id: Session ID (for ownership verification)

        Returns:
            True if deleted, False if not found/not owned
        """
        # Build ownership filter
        ownership_filter = self._build_ownership_filter(user_id, session_id)

        # Get the TODO with ownership verification
        result = await self.session.execute(
            select(TodoItem).where(
                TodoItem.id == todo_id,
                TodoItem.deleted_at.is_(None),
                ownership_filter
            )
        )
        todo = result.scalar_one_or_none()

        if not todo:
            return False

        todo.soft_delete()
        await self.session.commit()

        logger.info("TODO deleted", todo_id=str(todo_id))
        return True

    async def bulk_update_todos(self, bulk_update: TodoItemBulkUpdate,
                               user_id: Optional[UUID] = None, session_id: Optional[str] = None) -> BulkUpdateResponse:
        """
        Bulk update multiple TODO items.

        Args:
            bulk_update: Bulk update data
            user_id: User ID (for ownership verification)
            session_id: Session ID (for ownership verification)

        Returns:
            Number of items updated
        """
        # Build ownership filter
        ownership_filter = self._build_ownership_filter(user_id, session_id)

        # Build update data
        update_data: Dict[str, Any] = {"updated_at": datetime.utcnow()}

        if bulk_update.completed is not None:
            update_data["completed"] = bulk_update.completed
            if bulk_update.completed:
                update_data["completed_at"] = datetime.utcnow()
            else:
                update_data["completed_at"] = None

        if bulk_update.priority is not None:
            update_data["priority"] = bulk_update.priority

        # Execute bulk update
        result = await self.session.execute(
            update(TodoItem)
            .where(
                TodoItem.id.in_(bulk_update.todo_ids),
                TodoItem.deleted_at.is_(None),
                ownership_filter
            )
            .values(**update_data)
        )

        await self.session.commit()
        updated_count = result.rowcount or 0

        logger.info("Bulk TODO update completed", updated_count=updated_count)
        return BulkUpdateResponse(updated_count=updated_count)

    async def reorder_todos(self, reorder_data: TodoItemReorder,
                           user_id: Optional[UUID] = None, session_id: Optional[str] = None) -> BulkUpdateResponse:
        """
        Reorder TODO items by updating their order indices.

        Args:
            reorder_data: Reorder data with TODO IDs and new indices
            user_id: User ID (for ownership verification)
            session_id: Session ID (for ownership verification)

        Returns:
            Number of items reordered
        """
        # Build ownership filter
        ownership_filter = self._build_ownership_filter(user_id, session_id)

        updated_count = 0

        # Update each TODO's order index
        for todo_order in reorder_data.todo_orders:
            result = await self.session.execute(
                update(TodoItem)
                .where(
                    TodoItem.id == todo_order.todo_id,
                    TodoItem.deleted_at.is_(None),
                    ownership_filter
                )
                .values(
                    order_index=todo_order.order_index,
                    updated_at=datetime.utcnow()
                )
            )
            updated_count += result.rowcount or 0

        await self.session.commit()

        logger.info("TODO reorder completed", updated_count=updated_count)
        return BulkUpdateResponse(updated_count=updated_count)

    async def migrate_session_todos_to_user(self, session_id: str, user_id: UUID) -> int:
        """
        Migrate all TODOs from a guest session to a registered user.

        Args:
            session_id: Source session ID
            user_id: Target user ID

        Returns:
            Number of TODOs migrated
        """
        # Update all session TODOs to belong to the user
        result = await self.session.execute(
            update(TodoItem)
            .where(
                TodoItem.session_id == session_id,
                TodoItem.deleted_at.is_(None)
            )
            .values(
                user_id=user_id,
                session_id=None,
                updated_at=datetime.utcnow()
            )
        )

        await self.session.commit()
        migrated_count = result.rowcount or 0

        logger.info("Session TODOs migrated to user",
                   session_id=session_id, user_id=str(user_id), migrated_count=migrated_count)
        return migrated_count

    async def _get_next_order_index_for_user(self, user_id: UUID) -> int:
        """Get the next order index for a user's TODOs."""
        result = await self.session.execute(
            select(func.coalesce(func.max(TodoItem.order_index), -1))
            .where(
                TodoItem.user_id == user_id,
                TodoItem.deleted_at.is_(None)
            )
        )
        max_index = result.scalar() or -1
        return max_index + 1

    async def _get_next_order_index_for_session(self, session_id: str) -> int:
        """Get the next order index for a session's TODOs."""
        result = await self.session.execute(
            select(func.coalesce(func.max(TodoItem.order_index), -1))
            .where(
                TodoItem.session_id == session_id,
                TodoItem.deleted_at.is_(None)
            )
        )
        max_index = result.scalar() or -1
        return max_index + 1

    def _build_ownership_filter(self, user_id: Optional[UUID], session_id: Optional[str]):
        """Build SQLAlchemy filter for TODO ownership verification."""
        if user_id is not None:
            return TodoItem.user_id == user_id
        elif session_id is not None:
            return TodoItem.session_id == session_id
        else:
            # No ownership context provided - this should not happen in normal operation
            return False

    def to_response(self, todo: TodoItem) -> TodoItemResponse:
        """Convert TodoItem model to response schema."""
        return TodoItemResponse(
            id=todo.id,
            title=todo.title,
            description=todo.description,
            completed=todo.completed,
            completed_at=todo.completed_at,
            priority=todo.priority,
            order_index=todo.order_index,
            created_at=todo.created_at,
            updated_at=todo.updated_at
        )