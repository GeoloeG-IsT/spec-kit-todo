"""
Integration test for guest user workflow.

This test verifies the complete guest user experience as described in quickstart.md.
It MUST fail initially (TDD approach) and pass after full implementation.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import Response


@pytest.fixture
def client():
    """Test client for the FastAPI application."""
    # This will fail initially since the app doesn't exist yet
    from src.main import app
    return TestClient(app)


class TestGuestUserFlow:
    """Integration test for complete guest user workflow."""

    def test_complete_guest_workflow(self, client: TestClient):
        """
        Test the complete guest user flow from quickstart.md Scenario 1:
        1. Access application and get guest session
        2. Create multiple TODOs
        3. Manage TODOs (complete, edit, reorder, delete)
        4. Verify session persistence
        5. Verify session isolation
        """

        # Step 1: Create guest session
        session_response: Response = client.post("/api/auth/session", json={
            "user_agent": "Mozilla/5.0 Test Browser",
            "ip_address": "127.0.0.1"
        })
        assert session_response.status_code == 201
        session_data = session_response.json()
        session_id = session_data["id"]

        session_headers = {"X-Session-ID": session_id}

        # Step 2: Create 3 TODOs as specified in quickstart
        todo_1_response: Response = client.post("/api/todos", json={
            "title": "Test guest TODO 1",
            "priority": "high"
        }, headers=session_headers)
        assert todo_1_response.status_code == 201
        todo_1 = todo_1_response.json()

        todo_2_response: Response = client.post("/api/todos", json={
            "title": "Test guest TODO 2",
            "priority": "medium"
        }, headers=session_headers)
        assert todo_2_response.status_code == 201
        todo_2 = todo_2_response.json()

        todo_3_response: Response = client.post("/api/todos", json={
            "title": "Test guest TODO 3",
            "priority": "low"
        }, headers=session_headers)
        assert todo_3_response.status_code == 201
        todo_3 = todo_3_response.json()

        # Verify all TODOs are created
        list_response: Response = client.get("/api/todos", headers=session_headers)
        assert list_response.status_code == 200
        todos_data = list_response.json()
        assert todos_data["total"] == 3
        assert len(todos_data["items"]) == 3

        # Step 3: Manage TODOs

        # 3a. Mark one TODO as completed
        complete_response: Response = client.put(f"/api/todos/{todo_1['id']}", json={
            "completed": True
        }, headers=session_headers)
        assert complete_response.status_code == 200
        completed_todo = complete_response.json()
        assert completed_todo["completed"] is True
        assert completed_todo["completed_at"] is not None

        # 3b. Edit another TODO's title
        edit_response: Response = client.put(f"/api/todos/{todo_2['id']}", json={
            "title": "Updated guest TODO 2"
        }, headers=session_headers)
        assert edit_response.status_code == 200
        edited_todo = edit_response.json()
        assert edited_todo["title"] == "Updated guest TODO 2"

        # 3c. Reorder TODOs by updating order_index
        reorder_response: Response = client.put("/api/todos/reorder", json={
            "todo_orders": [
                {"todo_id": todo_3["id"], "order_index": 0},
                {"todo_id": todo_1["id"], "order_index": 1},
                {"todo_id": todo_2["id"], "order_index": 2}
            ]
        }, headers=session_headers)
        assert reorder_response.status_code == 200

        # 3d. Delete one TODO
        delete_response: Response = client.delete(f"/api/todos/{todo_3['id']}", headers=session_headers)
        assert delete_response.status_code == 204

        # Verify changes are reflected
        final_list_response: Response = client.get("/api/todos", headers=session_headers)
        assert final_list_response.status_code == 200
        final_todos = final_list_response.json()
        assert final_todos["total"] == 2  # One deleted

        # Find the completed and edited TODOs
        remaining_todos = final_todos["items"]
        completed_found = any(todo["completed"] for todo in remaining_todos)
        edited_found = any(todo["title"] == "Updated guest TODO 2" for todo in remaining_todos)
        assert completed_found, "Completed TODO not found"
        assert edited_found, "Edited TODO not found"

        # Step 4: Verify session persistence (simulate page refresh)
        # The same session should still have the TODOs
        refresh_list_response: Response = client.get("/api/todos", headers=session_headers)
        assert refresh_list_response.status_code == 200
        refresh_todos = refresh_list_response.json()
        assert refresh_todos["total"] == 2

        # Step 5: Verify session isolation
        # Create a new session and verify it doesn't see the first session's TODOs
        new_session_response: Response = client.post("/api/auth/session", json={
            "user_agent": "Different Browser"
        })
        assert new_session_response.status_code == 201
        new_session_data = new_session_response.json()
        new_session_headers = {"X-Session-ID": new_session_data["id"]}

        # New session should have no TODOs
        new_session_todos_response: Response = client.get("/api/todos", headers=new_session_headers)
        assert new_session_todos_response.status_code == 200
        new_session_todos = new_session_todos_response.json()
        assert new_session_todos["total"] == 0
        assert len(new_session_todos["items"]) == 0

    def test_guest_session_creation_workflow(self, client: TestClient):
        """Test guest session creation and basic TODO operations."""

        # Create session
        session_response: Response = client.post("/api/auth/session", json={})
        assert session_response.status_code == 201
        session_data = session_response.json()

        # Verify session response structure
        assert "id" in session_data
        assert "created_at" in session_data
        assert "last_accessed_at" in session_data

        session_headers = {"X-Session-ID": session_data["id"]}

        # Create TODO with session
        todo_response: Response = client.post("/api/todos", json={
            "title": "Session TODO",
            "description": "Testing session-based TODO creation"
        }, headers=session_headers)
        assert todo_response.status_code == 201

        # Verify TODO is associated with session
        list_response: Response = client.get("/api/todos", headers=session_headers)
        assert list_response.status_code == 200
        todos = list_response.json()
        assert todos["total"] == 1
        assert todos["items"][0]["title"] == "Session TODO"

    def test_guest_todos_priority_and_filtering(self, client: TestClient):
        """Test TODO priority levels and filtering for guest users."""

        # Create session
        session_response: Response = client.post("/api/auth/session", json={})
        session_data = session_response.json()
        session_headers = {"X-Session-ID": session_data["id"]}

        # Create TODOs with different priorities
        priorities = ["low", "medium", "high"]
        for i, priority in enumerate(priorities):
            todo_response: Response = client.post("/api/todos", json={
                "title": f"TODO {i+1}",
                "priority": priority
            }, headers=session_headers)
            assert todo_response.status_code == 201

        # Test filtering by priority
        for priority in priorities:
            filtered_response: Response = client.get(
                f"/api/todos?priority={priority}",
                headers=session_headers
            )
            assert filtered_response.status_code == 200
            filtered_todos = filtered_response.json()
            assert filtered_todos["total"] == 1
            assert filtered_todos["items"][0]["priority"] == priority

    def test_guest_todo_completion_workflow(self, client: TestClient):
        """Test TODO completion and filtering by completion status."""

        # Create session
        session_response: Response = client.post("/api/auth/session", json={})
        session_data = session_response.json()
        session_headers = {"X-Session-ID": session_data["id"]}

        # Create 2 TODOs
        todo_1_response: Response = client.post("/api/todos", json={
            "title": "TODO to complete"
        }, headers=session_headers)
        todo_1 = todo_1_response.json()

        todo_2_response: Response = client.post("/api/todos", json={
            "title": "TODO to keep pending"
        }, headers=session_headers)
        todo_2 = todo_2_response.json()

        # Complete one TODO
        complete_response: Response = client.put(f"/api/todos/{todo_1['id']}", json={
            "completed": True
        }, headers=session_headers)
        assert complete_response.status_code == 200

        # Filter completed TODOs
        completed_response: Response = client.get(
            "/api/todos?completed=true",
            headers=session_headers
        )
        assert completed_response.status_code == 200
        completed_todos = completed_response.json()
        assert completed_todos["total"] == 1
        assert completed_todos["items"][0]["completed"] is True

        # Filter pending TODOs
        pending_response: Response = client.get(
            "/api/todos?completed=false",
            headers=session_headers
        )
        assert pending_response.status_code == 200
        pending_todos = pending_response.json()
        assert pending_todos["total"] == 1
        assert pending_todos["items"][0]["completed"] is False

    def test_invalid_session_handling(self, client: TestClient):
        """Test behavior with invalid session IDs."""

        invalid_headers = {"X-Session-ID": "invalid_session_12345"}

        # Try to create TODO with invalid session
        todo_response: Response = client.post("/api/todos", json={
            "title": "Invalid session TODO"
        }, headers=invalid_headers)
        assert todo_response.status_code == 401

        # Try to list TODOs with invalid session
        list_response: Response = client.get("/api/todos", headers=invalid_headers)
        assert list_response.status_code == 401

    def test_guest_bulk_operations(self, client: TestClient):
        """Test bulk operations for guest users."""

        # Create session
        session_response: Response = client.post("/api/auth/session", json={})
        session_data = session_response.json()
        session_headers = {"X-Session-ID": session_data["id"]}

        # Create multiple TODOs
        todo_ids = []
        for i in range(3):
            todo_response: Response = client.post("/api/todos", json={
                "title": f"Bulk TODO {i+1}"
            }, headers=session_headers)
            todo_ids.append(todo_response.json()["id"])

        # Bulk complete all TODOs
        bulk_response: Response = client.put("/api/todos/bulk", json={
            "todo_ids": todo_ids,
            "completed": True
        }, headers=session_headers)
        assert bulk_response.status_code == 200
        bulk_result = bulk_response.json()
        assert bulk_result["updated_count"] == 3

        # Verify all are completed
        list_response: Response = client.get("/api/todos", headers=session_headers)
        todos = list_response.json()
        for todo in todos["items"]:
            assert todo["completed"] is True