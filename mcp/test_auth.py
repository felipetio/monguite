#!/usr/bin/env python3
"""
Test MCP server authentication and endpoints.
"""
import asyncio
import os

import httpx


async def test_health_endpoint():
    """Test health check endpoint (no auth required)."""
    print("\n=== Testing Health Endpoint ===")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:3000/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")

            if response.status_code == 200:
                print("✓ Health endpoint accessible without auth")
            else:
                print("✗ Unexpected status code")
        except Exception as e:
            print(f"✗ Error: {e}")


async def test_sse_without_auth():
    """Test SSE endpoint without authentication (should fail if API key is set)."""
    print("\n=== Testing SSE Endpoint Without Auth ===")

    api_key = os.getenv("MCP_API_KEY", "")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:3000/sse")
            print(f"Status: {response.status_code}")

            if api_key:
                if response.status_code == 401:
                    print("✓ Correctly rejected unauthenticated request")
                else:
                    print("✗ Should have rejected unauthenticated request")
            else:
                print("⚠ MCP_API_KEY not set - endpoint allows unauthenticated access")
        except Exception as e:
            print(f"✗ Error: {e}")


async def test_sse_with_invalid_auth():
    """Test SSE endpoint with invalid authentication."""
    print("\n=== Testing SSE Endpoint With Invalid Auth ===")

    api_key = os.getenv("MCP_API_KEY", "")

    if not api_key:
        print("⚠ Skipping - MCP_API_KEY not set")
        return

    headers = {"Authorization": "Bearer invalid-key-here"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:3000/sse", headers=headers)
            print(f"Status: {response.status_code}")

            if response.status_code == 401:
                print("✓ Correctly rejected invalid API key")
            else:
                print("✗ Should have rejected invalid API key")
        except Exception as e:
            print(f"✗ Error: {e}")


async def test_sse_with_valid_auth():
    """Test SSE endpoint with valid authentication."""
    print("\n=== Testing SSE Endpoint With Valid Auth ===")

    api_key = os.getenv("MCP_API_KEY", "")

    if not api_key:
        print("⚠ Skipping - MCP_API_KEY not set")
        return

    headers = {"Authorization": f"Bearer {api_key}"}

    async with httpx.AsyncClient() as client:
        try:
            # SSE endpoint will hang waiting for events, so we use a short timeout
            response = await client.get(
                "http://localhost:3000/sse", headers=headers, timeout=2.0
            )
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                print("✓ Successfully authenticated to SSE endpoint")
            else:
                print(f"✗ Unexpected status code: {response.status_code}")
        except httpx.ReadTimeout:
            # This is expected for SSE - connection established but no events sent
            print(
                "✓ Successfully authenticated (connection timeout is expected for SSE)"
            )
        except Exception as e:
            print(f"✗ Error: {e}")


async def test_messages_without_auth():
    """Test messages endpoint without authentication."""
    print("\n=== Testing Messages Endpoint Without Auth ===")

    api_key = os.getenv("MCP_API_KEY", "")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://localhost:3000/messages")
            print(f"Status: {response.status_code}")

            if api_key:
                if response.status_code == 401:
                    print("✓ Correctly rejected unauthenticated request")
                else:
                    print("✗ Should have rejected unauthenticated request")
            else:
                print("⚠ MCP_API_KEY not set - endpoint allows unauthenticated access")
        except Exception as e:
            print(f"✗ Error: {e}")


async def main():
    """Run all authentication tests."""
    print("=" * 50)
    print("MCP Server Authentication Tests")
    print("=" * 50)

    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            await client.get("http://localhost:3000/health", timeout=2.0)
    except Exception:
        print("\n✗ MCP server not running on http://localhost:3000")
        print("Start it with: MCP_TRANSPORT=http python mcp/server.py")
        return

    api_key = os.getenv("MCP_API_KEY", "")
    if api_key:
        print(f"\nMCP_API_KEY is set: {api_key[:8]}...")
    else:
        print("\n⚠ MCP_API_KEY not set - authentication tests will be limited")

    # Run tests
    await test_health_endpoint()
    await test_sse_without_auth()
    await test_sse_with_invalid_auth()
    await test_sse_with_valid_auth()
    await test_messages_without_auth()

    print("\n" + "=" * 50)
    print("Tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
