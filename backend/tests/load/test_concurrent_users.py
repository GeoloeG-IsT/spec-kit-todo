"""
Load tests for concurrent users
Testing the application under various load scenarios
"""
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List
import statistics

import httpx


class TestConcurrentUsers:
    """Load tests for concurrent user scenarios"""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture
    async def test_client(self):
        """HTTP client for load testing"""
        async with httpx.AsyncClient(base_url=self.BASE_URL, timeout=30.0) as client:
            yield client

    @pytest.mark.asyncio
    async def test_concurrent_guest_sessions(self, test_client):
        """Test concurrent guest session creation and usage"""
        concurrent_users = 50
        sessions_per_user = 5

        async def create_guest_session():
            """Create a guest session and perform basic operations"""
            session_data = {
                "user_agent": "LoadTest/1.0",
                "ip_address": "127.0.0.1"
            }

            start_time = time.time()

            # Create session
            response = await test_client.post("/api/auth/session", json=session_data)
            if response.status_code != 201:
                return {"success": False, "error": "Session creation failed"}

            session_id = response.json()["id"]
            headers = {"X-Session-ID": session_id}

            # Create multiple TODOs
            todos = []
            for i in range(sessions_per_user):
                todo_data = {
                    "title": f"Load Test TODO {i}",
                    "description": f"Description {i}",
                    "priority": "medium"
                }

                response = await test_client.post("/api/todos", json=todo_data, headers=headers)
                if response.status_code == 201:
                    todos.append(response.json()["id"])

            # Read TODOs
            response = await test_client.get("/api/todos", headers=headers)

            end_time = time.time()

            return {
                "success": response.status_code == 200,
                "duration": end_time - start_time,
                "todos_created": len(todos),
                "session_id": session_id
            }

        # Execute concurrent requests
        tasks = [create_guest_session() for _ in range(concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success", False)]

        assert len(successful_results) >= concurrent_users * 0.8, f"Only {len(successful_results)}/{concurrent_users} sessions succeeded"

        # Performance assertions
        avg_duration = statistics.mean([r["duration"] for r in successful_results])
        max_duration = max([r["duration"] for r in successful_results])

        print(f"Concurrent guest sessions: {len(successful_results)}/{concurrent_users} succeeded")
        print(f"Average duration: {avg_duration:.2f}s")
        print(f"Max duration: {max_duration:.2f}s")

        assert avg_duration < 10.0, f"Average session creation took too long: {avg_duration:.2f}s"
        assert max_duration < 30.0, f"Maximum session creation took too long: {max_duration:.2f}s"

    @pytest.mark.asyncio
    async def test_concurrent_authenticated_users(self, test_client):
        """Test concurrent authenticated user operations"""
        concurrent_users = 25
        todos_per_user = 10

        async def simulate_authenticated_user(user_index):
            """Simulate authenticated user operations"""
            # Use mock auth token for testing
            headers = {"Authorization": f"Bearer mock_token_user_{user_index}"}

            start_time = time.time()

            # Create user
            user_data = {
                "clerk_user_id": f"user_load_test_{user_index}",
                "display_name": f"Load Test User {user_index}"
            }

            response = await test_client.post("/api/auth/user", json=user_data, headers=headers)
            if response.status_code not in [200, 201]:
                return {"success": False, "error": "User creation failed"}

            # Create TODOs
            todos_created = 0
            for i in range(todos_per_user):
                todo_data = {
                    "title": f"User {user_index} TODO {i}",
                    "description": f"Load test description {i}",
                    "priority": "high" if i % 3 == 0 else "medium"
                }

                response = await test_client.post("/api/todos", json=todo_data, headers=headers)
                if response.status_code == 201:
                    todos_created += 1

            # Read and update TODOs
            response = await test_client.get("/api/todos", headers=headers)
            todos_fetched = 0
            if response.status_code == 200:
                todos = response.json().get("items", [])
                todos_fetched = len(todos)

                # Update first TODO if available
                if todos:
                    todo_id = todos[0]["id"]
                    update_data = {"completed": True}
                    await test_client.put(f"/api/todos/{todo_id}", json=update_data, headers=headers)

            end_time = time.time()

            return {
                "success": True,
                "duration": end_time - start_time,
                "todos_created": todos_created,
                "todos_fetched": todos_fetched,
                "user_index": user_index
            }

        # Execute concurrent requests
        tasks = [simulate_authenticated_user(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success", False)]

        assert len(successful_results) >= concurrent_users * 0.8, f"Only {len(successful_results)}/{concurrent_users} users succeeded"

        # Performance assertions
        avg_duration = statistics.mean([r["duration"] for r in successful_results])
        max_duration = max([r["duration"] for r in successful_results])
        total_todos_created = sum([r["todos_created"] for r in successful_results])

        print(f"Concurrent authenticated users: {len(successful_results)}/{concurrent_users} succeeded")
        print(f"Average duration: {avg_duration:.2f}s")
        print(f"Max duration: {max_duration:.2f}s")
        print(f"Total TODOs created: {total_todos_created}")

        assert avg_duration < 15.0, f"Average user operations took too long: {avg_duration:.2f}s"
        assert max_duration < 45.0, f"Maximum user operations took too long: {max_duration:.2f}s"

    @pytest.mark.asyncio
    async def test_mixed_load_scenario(self, test_client):
        """Test mixed load with both guest and authenticated users"""
        guest_users = 30
        auth_users = 20

        async def create_mixed_load():
            """Create mixed load scenario"""
            guest_tasks = []
            auth_tasks = []

            # Guest user operations
            async def guest_operation(index):
                session_data = {"user_agent": f"Guest{index}", "ip_address": "127.0.0.1"}
                response = await test_client.post("/api/auth/session", json=session_data)
                if response.status_code == 201:
                    session_id = response.json()["id"]
                    headers = {"X-Session-ID": session_id}

                    # Create a few TODOs
                    for i in range(3):
                        todo_data = {"title": f"Guest {index} TODO {i}", "priority": "low"}
                        await test_client.post("/api/todos", json=todo_data, headers=headers)

                    return {"type": "guest", "success": True}
                return {"type": "guest", "success": False}

            # Authenticated user operations
            async def auth_operation(index):
                headers = {"Authorization": f"Bearer mock_token_mixed_{index}"}
                user_data = {
                    "clerk_user_id": f"user_mixed_{index}",
                    "display_name": f"Mixed User {index}"
                }

                response = await test_client.post("/api/auth/user", json=user_data, headers=headers)
                if response.status_code in [200, 201]:
                    # Create TODOs
                    for i in range(2):
                        todo_data = {"title": f"Auth {index} TODO {i}", "priority": "high"}
                        await test_client.post("/api/todos", json=todo_data, headers=headers)

                    return {"type": "auth", "success": True}
                return {"type": "auth", "success": False}

            # Create tasks
            guest_tasks = [guest_operation(i) for i in range(guest_users)]
            auth_tasks = [auth_operation(i) for i in range(auth_users)]

            all_tasks = guest_tasks + auth_tasks

            start_time = time.time()
            results = await asyncio.gather(*all_tasks, return_exceptions=True)
            end_time = time.time()

            return results, end_time - start_time

        results, total_duration = await create_mixed_load()

        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success", False)]
        guest_successes = len([r for r in successful_results if r["type"] == "guest"])
        auth_successes = len([r for r in successful_results if r["type"] == "auth"])

        total_users = guest_users + auth_users
        success_rate = len(successful_results) / total_users

        print(f"Mixed load test results:")
        print(f"Total duration: {total_duration:.2f}s")
        print(f"Guest users: {guest_successes}/{guest_users} succeeded")
        print(f"Auth users: {auth_successes}/{auth_users} succeeded")
        print(f"Overall success rate: {success_rate:.2%}")

        assert success_rate >= 0.8, f"Success rate too low: {success_rate:.2%}"
        assert total_duration < 60.0, f"Mixed load test took too long: {total_duration:.2f}s"

    @pytest.mark.asyncio
    async def test_real_time_sync_under_load(self, test_client):
        """Test real-time sync performance under load"""
        concurrent_connections = 20
        messages_per_connection = 10

        async def simulate_sse_connection(connection_index):
            """Simulate SSE connection with concurrent TODO operations"""
            # Use mock auth for testing
            headers = {"Authorization": f"Bearer mock_token_sse_{connection_index}"}

            try:
                # Create user first
                user_data = {
                    "clerk_user_id": f"user_sse_{connection_index}",
                    "display_name": f"SSE User {connection_index}"
                }
                await test_client.post("/api/auth/user", json=user_data, headers=headers)

                # Connect to SSE stream (simulate with timeout)
                start_time = time.time()

                # Simulate rapid TODO operations while "connected" to SSE
                operations_completed = 0
                for i in range(messages_per_connection):
                    todo_data = {
                        "title": f"SSE Test TODO {connection_index}-{i}",
                        "priority": "medium"
                    }

                    response = await test_client.post("/api/todos", json=todo_data, headers=headers)
                    if response.status_code == 201:
                        operations_completed += 1

                        # Simulate some operations
                        if i % 3 == 0:
                            todo_id = response.json()["id"]
                            update_data = {"completed": True}
                            await test_client.put(f"/api/todos/{todo_id}", json=update_data, headers=headers)

                end_time = time.time()

                return {
                    "success": True,
                    "duration": end_time - start_time,
                    "operations_completed": operations_completed,
                    "connection_index": connection_index
                }

            except Exception as e:
                return {"success": False, "error": str(e)}

        # Execute concurrent SSE simulations
        tasks = [simulate_sse_connection(i) for i in range(concurrent_connections)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success", False)]

        assert len(successful_results) >= concurrent_connections * 0.8, f"Only {len(successful_results)}/{concurrent_connections} SSE connections succeeded"

        # Performance assertions
        avg_duration = statistics.mean([r["duration"] for r in successful_results])
        total_operations = sum([r["operations_completed"] for r in successful_results])

        print(f"SSE load test results:")
        print(f"Successful connections: {len(successful_results)}/{concurrent_connections}")
        print(f"Average duration: {avg_duration:.2f}s")
        print(f"Total operations: {total_operations}")

        assert avg_duration < 20.0, f"SSE operations took too long: {avg_duration:.2f}s"