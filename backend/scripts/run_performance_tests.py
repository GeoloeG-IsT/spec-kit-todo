#!/usr/bin/env python3
"""
Performance test runner script
Starts the API server and runs performance tests
"""

import asyncio
import subprocess
import time
import sys
import os
import signal
from pathlib import Path
import httpx

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

API_SERVER_URL = "http://localhost:8000"
API_SERVER_CMD = ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]


async def wait_for_server(url: str, timeout: int = 30) -> bool:
    """Wait for the API server to be ready"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    print(f"✅ API server is ready at {url}")
                    return True
        except (httpx.ConnectError, httpx.TimeoutException):
            print(f"⏳ Waiting for API server at {url}...")
            await asyncio.sleep(2)

    return False


def start_api_server():
    """Start the API server in background"""
    print("🚀 Starting API server...")

    # Change to backend directory
    backend_dir = Path(__file__).parent.parent

    # Start server with proper environment
    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend_dir)

    process = subprocess.Popen(
        API_SERVER_CMD,
        cwd=backend_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid  # Create new process group
    )

    return process


def stop_api_server(process):
    """Stop the API server"""
    if process:
        print("🛑 Stopping API server...")
        try:
            # Kill the entire process group
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=10)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass


async def run_performance_tests():
    """Run the performance tests"""
    backend_dir = Path(__file__).parent.parent

    # Run pytest on performance tests
    cmd = [
        "python", "-m", "pytest",
        "tests/performance/",
        "-v", "-s",  # Verbose output and don't capture stdout
        "--tb=short"  # Shorter traceback format
    ]

    print("📊 Running performance tests...")
    process = subprocess.run(
        cmd,
        cwd=backend_dir,
        capture_output=False  # Let output go to console
    )

    return process.returncode


async def main():
    """Main function to orchestrate performance testing"""
    server_process = None

    try:
        # Start API server
        server_process = start_api_server()

        # Wait for server to be ready
        if not await wait_for_server(API_SERVER_URL):
            print("❌ API server failed to start within timeout")
            return 1

        # Run performance tests
        result = await run_performance_tests()

        if result == 0:
            print("✅ All performance tests passed!")
        else:
            print(f"❌ Performance tests failed with exit code {result}")

        return result

    except KeyboardInterrupt:
        print("\n⏸️  Performance testing interrupted by user")
        return 1

    except Exception as e:
        print(f"❌ Error during performance testing: {e}")
        return 1

    finally:
        # Always stop the server
        if server_process:
            stop_api_server(server_process)


if __name__ == "__main__":
    # Set up signal handlers for clean shutdown
    def signal_handler(signum, frame):
        _ = frame  # Mark frame as used to avoid warning
        print(f"\n🛑 Received signal {signum}, shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the performance tests
    exit_code = asyncio.run(main())
    sys.exit(exit_code)