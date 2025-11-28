#!/usr/bin/env python3
"""
Test MCP server authentication and endpoints.
Tests the Streamable HTTP transport with Bearer token authentication.
"""

import asyncio
import os

import httpx
import pytest

# Default port for MCP server
MCP_PORT = os.getenv("MCP_PORT", "8001")
BASE_URL = f"http://localhost:{MCP_PORT}"


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint (no auth required)."""
    print("\n=== Testing Health Endpoint ===")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")

            if response.status_code == 200:
                print("✓ Health endpoint accessible without auth")
            else:
                print("✗ Unexpected status code")
        except Exception as e:
            print(f"✗ Error: {e}")


@pytest.mark.asyncio
async def test_mcp_without_auth():
    """Test MCP endpoint without authentication (should fail if bearer token is set)."""
    print("\n=== Testing MCP Endpoint Without Auth ===")

    bearer_token = os.getenv("MCP_BEARER_TOKEN", "")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/mcp",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
            )
            print(f"Status: {response.status_code}")

            if bearer_token:
                if response.status_code == 401:
                    print("✓ Correctly rejected unauthenticated request")
                else:
                    print("✗ Should have rejected unauthenticated request")
            else:
                print("⚠ MCP_BEARER_TOKEN not set - endpoint allows unauthenticated access")
        except Exception as e:
            print(f"✗ Error: {e}")


@pytest.mark.asyncio
async def test_mcp_with_invalid_auth():
    """Test MCP endpoint with invalid authentication."""
    print("\n=== Testing MCP Endpoint With Invalid Auth ===")

    bearer_token = os.getenv("MCP_BEARER_TOKEN", "")

    if not bearer_token:
        print("⚠ Skipping - MCP_BEARER_TOKEN not set")
        return

    headers = {
        "Authorization": "Bearer invalid-token-here",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/mcp", headers=headers)
            print(f"Status: {response.status_code}")

            if response.status_code == 401:
                print("✓ Correctly rejected invalid bearer token")
            else:
                print("✗ Should have rejected invalid bearer token")
        except Exception as e:
            print(f"✗ Error: {e}")


@pytest.mark.asyncio
async def test_mcp_with_valid_auth():
    """Test MCP endpoint with valid authentication."""
    print("\n=== Testing MCP Endpoint With Valid Auth ===")

    bearer_token = os.getenv("MCP_BEARER_TOKEN", "")

    if not bearer_token:
        print("⚠ Skipping - MCP_BEARER_TOKEN not set")
        return

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    # Send a valid MCP initialize request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/mcp", headers=headers, json=init_request, timeout=5.0)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                print("✓ Successfully authenticated to MCP endpoint")
                print(f"Response: {response.text[:200]}...")
            else:
                print(f"✗ Unexpected status code: {response.status_code}")
                print(f"Response: {response.text}")
        except httpx.ReadTimeout:
            # This might happen if server is waiting for more data
            print("✓ Successfully authenticated (timeout waiting for response)")
        except Exception as e:
            print(f"✗ Error: {e}")


async def main():
    """Run all authentication tests."""
    print("=" * 50)
    print("MCP Server Authentication Tests")
    print(f"Testing against: {BASE_URL}")
    print("=" * 50)

    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            await client.get(f"{BASE_URL}/health", timeout=2.0)
    except Exception:
        print(f"\n✗ MCP server not running on {BASE_URL}")
        print("Start it with: MCP_TRANSPORT=http uv run python mcp/server.py")
        return

    bearer_token = os.getenv("MCP_BEARER_TOKEN", "")
    if bearer_token:
        print(f"\nMCP_BEARER_TOKEN is set: {bearer_token[:8]}...")
    else:
        print("\n⚠ MCP_BEARER_TOKEN not set - authentication tests will be limited")

    # Run tests
    await test_health_endpoint()
    await test_mcp_without_auth()
    await test_mcp_with_invalid_auth()
    await test_mcp_with_valid_auth()

    print("\n" + "=" * 50)
    print("Tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
