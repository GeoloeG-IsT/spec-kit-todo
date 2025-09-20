"""
Simple backend test to verify the test framework is working
"""

import pytest
from unittest.mock import Mock, AsyncMock


class TestSimpleBackend:
    """Simple backend tests to verify framework"""

    def test_basic_functionality(self):
        """Test basic Python functionality"""
        assert 1 + 1 == 2
        assert "hello" + " world" == "hello world"

    def test_mock_functionality(self):
        """Test that mocking works"""
        mock = Mock()
        mock.return_value = "test"
        assert mock() == "test"

    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality"""
        async def async_func():
            return "async result"

        result = await async_func()
        assert result == "async result"

    def test_pytest_fixtures(self, tmp_path):
        """Test that pytest fixtures work"""
        assert tmp_path.exists()
        assert tmp_path.is_dir()

    def test_environment_variables(self):
        """Test environment setup"""
        import os
        # Just test that we can access environment
        database_url = os.getenv("DATABASE_URL", "default")
        assert isinstance(database_url, str)

    def test_imports_work(self):
        """Test that our imports work"""
        from src.domain.models.todo_item import TodoItem, TodoPriority
        from src.domain.schemas import TodoItemCreate

        # Test enum
        assert TodoPriority.HIGH == "high"
        assert TodoPriority.MEDIUM == "medium"
        assert TodoPriority.LOW == "low"

        # Test schema creation
        todo_create = TodoItemCreate(title="Test TODO")
        assert todo_create.title == "Test TODO"
        assert todo_create.priority == "medium"  # default

    def test_pydantic_validation(self):
        """Test Pydantic validation works"""
        from src.domain.schemas import TodoItemCreate
        from pydantic import ValidationError

        # Valid creation
        todo = TodoItemCreate(title="Valid TODO")
        assert todo.title == "Valid TODO"

        # Invalid creation should raise ValidationError
        with pytest.raises(ValidationError):
            TodoItemCreate(title="")  # Empty title should fail

        with pytest.raises(ValidationError):
            TodoItemCreate()  # Missing required title

    def test_uuid_generation(self):
        """Test UUID functionality"""
        from uuid import uuid4

        id1 = uuid4()
        id2 = uuid4()

        assert id1 != id2
        assert str(id1)  # Can convert to string
        assert len(str(id1)) == 36  # Standard UUID format

    def test_datetime_functionality(self):
        """Test datetime functionality"""
        from datetime import datetime

        now = datetime.utcnow()
        assert isinstance(now, datetime)
        assert now.year >= 2025

    @pytest.mark.asyncio
    async def test_async_mock(self):
        """Test async mocking"""
        mock = AsyncMock()
        mock.return_value = "async mock result"

        result = await mock()
        assert result == "async mock result"