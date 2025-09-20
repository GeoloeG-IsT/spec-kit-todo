"""
Performance tests for TODO API endpoints
Testing response times and load handling
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import httpx
import pytest
from uuid import uuid4


class TestAPIPerformance:
    """Performance tests for API endpoints"""

    BASE_URL = "http://localhost:8000"
    PERFORMANCE_THRESHOLDS = {
        "create_todo": 200,  # ms
        "get_todos": 100,   # ms
        "update_todo": 150,  # ms
        "delete_todo": 100,  # ms
        "bulk_update": 500,  # ms
    }

    @pytest.fixture
    def session_headers(self):
        """Create headers with session ID"""
        return {
            "X-Session-ID": f"perf-test-session-{uuid4()}",
            "Content-Type": "application/json",
        }

    async def measure_response_time(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        json_data: Dict[str, Any] = None,
        repeat: int = 10
    ) -> Dict[str, float]:
        """Measure response time for an API call"""
        times = []

        async with httpx.AsyncClient() as client:
            for _ in range(repeat):
                start = time.perf_counter()

                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=json_data)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=json_data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)

                end = time.perf_counter()

                if response.status_code in [200, 201, 204]:
                    times.append((end - start) * 1000)  # Convert to ms

        return {
            "min": min(times) if times else 0,
            "max": max(times) if times else 0,
            "mean": statistics.mean(times) if times else 0,
            "median": statistics.median(times) if times else 0,
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        }

    @pytest.mark.asyncio
    async def test_create_todo_performance(self, session_headers):
        """Test TODO creation performance"""
        todo_data = {
            "title": "Performance test TODO",
            "description": "Testing creation speed",
            "priority": "medium",
        }

        stats = await self.measure_response_time(
            "POST",
            f"{self.BASE_URL}/api/todos",
            session_headers,
            todo_data,
            repeat=20
        )

        print(f"\nCreate TODO Performance:")
        print(f"  Min: {stats['min']:.2f}ms")
        print(f"  Max: {stats['max']:.2f}ms")
        print(f"  Mean: {stats['mean']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
        print(f"  StdDev: {stats['stdev']:.2f}ms")

        # Check against threshold
        assert stats['median'] < self.PERFORMANCE_THRESHOLDS['create_todo'], \
            f"Create TODO median response time {stats['median']:.2f}ms exceeds threshold {self.PERFORMANCE_THRESHOLDS['create_todo']}ms"

    @pytest.mark.asyncio
    async def test_get_todos_performance(self, session_headers):
        """Test TODO list retrieval performance"""
        # First, create some TODOs
        async with httpx.AsyncClient() as client:
            for i in range(50):
                await client.post(
                    f"{self.BASE_URL}/api/todos",
                    headers=session_headers,
                    json={"title": f"TODO {i}", "priority": "medium"}
                )

        # Measure GET performance
        stats = await self.measure_response_time(
            "GET",
            f"{self.BASE_URL}/api/todos",
            session_headers,
            repeat=20
        )

        print(f"\nGet TODOs Performance (50 items):")
        print(f"  Min: {stats['min']:.2f}ms")
        print(f"  Max: {stats['max']:.2f}ms")
        print(f"  Mean: {stats['mean']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
        print(f"  StdDev: {stats['stdev']:.2f}ms")

        assert stats['median'] < self.PERFORMANCE_THRESHOLDS['get_todos'], \
            f"Get TODOs median response time {stats['median']:.2f}ms exceeds threshold {self.PERFORMANCE_THRESHOLDS['get_todos']}ms"

    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, session_headers):
        """Test API performance under concurrent load"""
        concurrent_users = 10
        requests_per_user = 5

        async def user_workflow(user_id: int):
            """Simulate a user workflow"""
            user_headers = {
                **session_headers,
                "X-Session-ID": f"concurrent-user-{user_id}",
            }

            results = []
            async with httpx.AsyncClient() as client:
                for i in range(requests_per_user):
                    # Create TODO
                    start = time.perf_counter()
                    resp = await client.post(
                        f"{self.BASE_URL}/api/todos",
                        headers=user_headers,
                        json={"title": f"User {user_id} TODO {i}", "priority": "high"}
                    )
                    create_time = (time.perf_counter() - start) * 1000

                    if resp.status_code == 201:
                        todo_id = resp.json()["id"]

                        # Get TODOs
                        start = time.perf_counter()
                        await client.get(f"{self.BASE_URL}/api/todos", headers=user_headers)
                        get_time = (time.perf_counter() - start) * 1000

                        # Update TODO
                        start = time.perf_counter()
                        await client.put(
                            f"{self.BASE_URL}/api/todos/{todo_id}",
                            headers=user_headers,
                            json={"completed": True}
                        )
                        update_time = (time.perf_counter() - start) * 1000

                        results.append({
                            "create": create_time,
                            "get": get_time,
                            "update": update_time,
                        })

            return results

        # Run concurrent users
        start_time = time.perf_counter()
        tasks = [user_workflow(i) for i in range(concurrent_users)]
        all_results = await asyncio.gather(*tasks)
        total_time = (time.perf_counter() - start_time) * 1000

        # Flatten results
        flat_results = [r for user_results in all_results for r in user_results]

        # Calculate statistics
        create_times = [r["create"] for r in flat_results]
        get_times = [r["get"] for r in flat_results]
        update_times = [r["update"] for r in flat_results]

        print(f"\nConcurrent Load Test ({concurrent_users} users, {requests_per_user} requests each):")
        print(f"  Total Time: {total_time:.2f}ms")
        print(f"  Requests/sec: {(len(flat_results) * 3) / (total_time / 1000):.2f}")
        print(f"  Create TODO median: {statistics.median(create_times):.2f}ms")
        print(f"  Get TODOs median: {statistics.median(get_times):.2f}ms")
        print(f"  Update TODO median: {statistics.median(update_times):.2f}ms")

        # Check that performance doesn't degrade too much under load
        assert statistics.median(create_times) < self.PERFORMANCE_THRESHOLDS['create_todo'] * 2
        assert statistics.median(get_times) < self.PERFORMANCE_THRESHOLDS['get_todos'] * 2
        assert statistics.median(update_times) < self.PERFORMANCE_THRESHOLDS['update_todo'] * 2

    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self, session_headers):
        """Test bulk operations performance"""
        # Create many TODOs
        todo_ids = []
        async with httpx.AsyncClient() as client:
            for i in range(100):
                resp = await client.post(
                    f"{self.BASE_URL}/api/todos",
                    headers=session_headers,
                    json={"title": f"Bulk TODO {i}", "priority": "low"}
                )
                if resp.status_code == 201:
                    todo_ids.append(resp.json()["id"])

        # Test bulk update performance
        bulk_data = {
            "todo_ids": todo_ids[:50],  # Update 50 TODOs
            "completed": True,
            "priority": "high",
        }

        stats = await self.measure_response_time(
            "POST",
            f"{self.BASE_URL}/api/todos/bulk-update",
            session_headers,
            bulk_data,
            repeat=10
        )

        print(f"\nBulk Update Performance (50 items):")
        print(f"  Min: {stats['min']:.2f}ms")
        print(f"  Max: {stats['max']:.2f}ms")
        print(f"  Mean: {stats['mean']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
        print(f"  StdDev: {stats['stdev']:.2f}ms")

        assert stats['median'] < self.PERFORMANCE_THRESHOLDS['bulk_update'], \
            f"Bulk update median response time {stats['median']:.2f}ms exceeds threshold {self.PERFORMANCE_THRESHOLDS['bulk_update']}ms"

    @pytest.mark.asyncio
    async def test_database_query_optimization(self, session_headers):
        """Test database query performance with various filters"""
        # Create TODOs with different attributes
        async with httpx.AsyncClient() as client:
            priorities = ["low", "medium", "high"]
            for i in range(150):
                await client.post(
                    f"{self.BASE_URL}/api/todos",
                    headers=session_headers,
                    json={
                        "title": f"Query test TODO {i}",
                        "priority": priorities[i % 3],
                        "completed": i % 2 == 0,
                    }
                )

        # Test different query scenarios
        queries = [
            ("All TODOs", ""),
            ("Completed only", "?completed=true"),
            ("Active only", "?completed=false"),
            ("High priority", "?priority=high"),
            ("Combined filters", "?completed=false&priority=high"),
            ("With pagination", "?limit=10&offset=50"),
        ]

        for query_name, params in queries:
            stats = await self.measure_response_time(
                "GET",
                f"{self.BASE_URL}/api/todos{params}",
                session_headers,
                repeat=10
            )

            print(f"\n{query_name} Query Performance:")
            print(f"  Median: {stats['median']:.2f}ms")

            # All queries should be fast
            assert stats['median'] < 200, \
                f"{query_name} query too slow: {stats['median']:.2f}ms"

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, session_headers):
        """Test memory usage doesn't grow excessively under load"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create many requests
        async with httpx.AsyncClient() as client:
            for i in range(500):
                await client.post(
                    f"{self.BASE_URL}/api/todos",
                    headers=session_headers,
                    json={"title": f"Memory test {i}", "priority": "medium"}
                )

                if i % 100 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    print(f"Memory after {i} requests: {current_memory:.2f}MB")

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        print(f"\nMemory Usage:")
        print(f"  Initial: {initial_memory:.2f}MB")
        print(f"  Final: {final_memory:.2f}MB")
        print(f"  Increase: {memory_increase:.2f}MB")

        # Memory increase should be reasonable
        assert memory_increase < 100, \
            f"Memory usage increased by {memory_increase:.2f}MB, possible memory leak"

    @pytest.mark.asyncio
    async def test_sse_connection_performance(self, session_headers):
        """Test Server-Sent Events connection performance"""
        connection_times = []

        for _ in range(10):
            start = time.perf_counter()

            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "GET",
                    f"{self.BASE_URL}/api/todos/stream",
                    headers=session_headers,
                    timeout=5.0
                ) as response:
                    connection_time = (time.perf_counter() - start) * 1000
                    connection_times.append(connection_time)

                    # Read first event
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            break

        median_connection = statistics.median(connection_times)
        print(f"\nSSE Connection Performance:")
        print(f"  Median connection time: {median_connection:.2f}ms")

        assert median_connection < 100, \
            f"SSE connection time {median_connection:.2f}ms too slow"


class TestLoadScenarios:
    """Load testing scenarios"""

    BASE_URL = "http://localhost:8000"

    @pytest.mark.asyncio
    async def test_sustained_load(self):
        """Test API under sustained load for 1 minute"""
        duration = 60  # seconds
        requests_per_second = 10

        start_time = time.time()
        request_count = 0
        errors = 0
        response_times = []

        async with httpx.AsyncClient() as client:
            while time.time() - start_time < duration:
                batch_start = time.perf_counter()

                # Send batch of requests
                tasks = []
                for _ in range(requests_per_second):
                    session_id = f"load-test-{uuid4()}"
                    headers = {"X-Session-ID": session_id}

                    task = client.post(
                        f"{self.BASE_URL}/api/todos",
                        headers=headers,
                        json={"title": f"Load test {request_count}", "priority": "medium"}
                    )
                    tasks.append(task)
                    request_count += 1

                # Wait for all requests in batch
                responses = await asyncio.gather(*tasks, return_exceptions=True)

                # Count errors
                for resp in responses:
                    if isinstance(resp, Exception):
                        errors += 1
                    elif resp.status_code >= 400:
                        errors += 1

                batch_time = (time.perf_counter() - batch_start) * 1000
                response_times.append(batch_time)

                # Wait to maintain rate
                elapsed = time.time() - start_time
                expected_requests = int(elapsed * requests_per_second)
                if request_count < expected_requests:
                    await asyncio.sleep(0.01)

        # Calculate statistics
        error_rate = (errors / request_count) * 100 if request_count > 0 else 0
        avg_batch_time = statistics.mean(response_times)

        print(f"\nSustained Load Test Results:")
        print(f"  Duration: {duration}s")
        print(f"  Total Requests: {request_count}")
        print(f"  Errors: {errors} ({error_rate:.2f}%)")
        print(f"  Avg Batch Time: {avg_batch_time:.2f}ms")
        print(f"  Requests/sec: {request_count / duration:.2f}")

        assert error_rate < 1, f"Error rate {error_rate:.2f}% too high"
        assert avg_batch_time < 1000, f"Batch processing too slow: {avg_batch_time:.2f}ms"

    @pytest.mark.asyncio
    async def test_spike_load(self):
        """Test API behavior during traffic spikes"""
        normal_rps = 5
        spike_rps = 50
        normal_duration = 10
        spike_duration = 5

        async def send_requests(rate: int, duration: int, label: str):
            start = time.time()
            responses = []

            async with httpx.AsyncClient() as client:
                while time.time() - start < duration:
                    tasks = []
                    for _ in range(rate):
                        headers = {"X-Session-ID": f"spike-{uuid4()}"}
                        task = client.get(f"{self.BASE_URL}/api/todos", headers=headers)
                        tasks.append(task)

                    batch_start = time.perf_counter()
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    batch_time = (time.perf_counter() - batch_start) * 1000

                    success = sum(1 for r in results if not isinstance(r, Exception) and r.status_code == 200)
                    responses.append({
                        "time": batch_time,
                        "success": success,
                        "total": len(results),
                    })

                    await asyncio.sleep(1)

            return responses

        # Normal load
        print("\nStarting normal load...")
        normal_results = await send_requests(normal_rps, normal_duration, "normal")

        # Spike load
        print("Starting spike load...")
        spike_results = await send_requests(spike_rps, spike_duration, "spike")

        # Return to normal
        print("Returning to normal load...")
        recovery_results = await send_requests(normal_rps, normal_duration, "recovery")

        # Analyze results
        normal_avg = statistics.mean([r["time"] for r in normal_results])
        spike_avg = statistics.mean([r["time"] for r in spike_results])
        recovery_avg = statistics.mean([r["time"] for r in recovery_results])

        print(f"\nSpike Load Test Results:")
        print(f"  Normal avg response: {normal_avg:.2f}ms")
        print(f"  Spike avg response: {spike_avg:.2f}ms")
        print(f"  Recovery avg response: {recovery_avg:.2f}ms")

        # API should handle spike and recover
        assert spike_avg < normal_avg * 10, "Response time degraded too much during spike"
        assert recovery_avg < normal_avg * 1.5, "API didn't recover after spike"