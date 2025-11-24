#!/usr/bin/env python3
"""
Test OAuth 2.0 authentication for Monguite MCP Server
"""

import asyncio
import json
import os
import sys

import httpx

# Test configuration
MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:8001")
TEST_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "test-client")
TEST_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET", "test-secret")


def print_test(name: str):
    """Print test name."""
    print(f"\n{'=' * 60}")
    print(f"TEST: {name}")
    print("=" * 60)


def print_success(message: str):
    """Print success message."""
    print(f"✓ {message}")


def print_error(message: str):
    """Print error message."""
    print(f"✗ {message}")


async def test_oauth_token_endpoint():
    """Test the OAuth token endpoint."""
    print_test("OAuth Token Endpoint")

    async with httpx.AsyncClient() as client:
        try:
            # Test: Request token with valid credentials
            print("\n1. Testing token request with valid credentials...")
            response = await client.post(
                f"{MCP_BASE_URL}/oauth/token",
                headers={"Content-Type": "application/json"},
                json={
                    "grant_type": "client_credentials",
                    "client_id": TEST_CLIENT_ID,
                    "client_secret": TEST_CLIENT_SECRET,
                },
            )

            if response.status_code == 200:
                token_data = response.json()
                print_success("Token endpoint accessible")
                print(f"   Response: {json.dumps(token_data, indent=2)}")

                # Validate response structure
                required_fields = ["access_token", "token_type", "expires_in"]
                if all(field in token_data for field in required_fields):
                    print_success("Token response has all required fields")
                    return token_data["access_token"]
                else:
                    print_error(f"Missing fields. Expected: {required_fields}, Got: {list(token_data.keys())}")
                    return None
            else:
                print_error(f"Token request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

        except httpx.ConnectError:
            print_error("Cannot connect to MCP server")
            print("   Make sure server is running: MCP_TRANSPORT=http OAUTH_ENABLED=true uv run python mcp/server.py")
            return None
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            return None


async def test_invalid_credentials():
    """Test token endpoint with invalid credentials."""
    print_test("Invalid Credentials")

    async with httpx.AsyncClient() as client:
        try:
            print("\n1. Testing with invalid client_id...")
            response = await client.post(
                f"{MCP_BASE_URL}/oauth/token",
                headers={"Content-Type": "application/json"},
                json={
                    "grant_type": "client_credentials",
                    "client_id": "wrong-client-id",
                    "client_secret": TEST_CLIENT_SECRET,
                },
            )

            if response.status_code == 401:
                print_success("Correctly rejected invalid client_id (401)")
            else:
                print_error(f"Expected 401, got {response.status_code}")

            print("\n2. Testing with invalid client_secret...")
            response = await client.post(
                f"{MCP_BASE_URL}/oauth/token",
                headers={"Content-Type": "application/json"},
                json={
                    "grant_type": "client_credentials",
                    "client_id": TEST_CLIENT_ID,
                    "client_secret": "wrong-secret",
                },
            )

            if response.status_code == 401:
                print_success("Correctly rejected invalid client_secret (401)")
            else:
                print_error(f"Expected 401, got {response.status_code}")

            print("\n3. Testing with unsupported grant_type...")
            response = await client.post(
                f"{MCP_BASE_URL}/oauth/token",
                headers={"Content-Type": "application/json"},
                json={
                    "grant_type": "authorization_code",
                    "client_id": TEST_CLIENT_ID,
                    "client_secret": TEST_CLIENT_SECRET,
                },
            )

            if response.status_code == 400:
                print_success("Correctly rejected unsupported grant_type (400)")
                error_data = response.json()
                if error_data.get("error") == "unsupported_grant_type":
                    print_success("Error response has correct error code")
            else:
                print_error(f"Expected 400, got {response.status_code}")

        except Exception as e:
            print_error(f"Test failed: {e}")


async def test_token_authentication(access_token: str):
    """Test using the access token for authentication."""
    print_test("Token Authentication")

    async with httpx.AsyncClient() as client:
        try:
            print("\n1. Testing health endpoint with valid token...")
            response = await client.get(
                f"{MCP_BASE_URL}/health",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code == 200:
                print_success("Health endpoint accessible with token")
                health_data = response.json()
                print(f"   OAuth enabled: {health_data.get('oauth_enabled')}")
            else:
                print_error(f"Health check failed: {response.status_code}")

            print("\n2. Testing SSE endpoint with valid token...")
            # Note: SSE endpoint requires MCP protocol, just checking auth works
            response = await client.get(
                f"{MCP_BASE_URL}/sse",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            # We expect the SSE connection to start (any 2xx code is fine for this test)
            if response.status_code < 400:
                print_success("SSE endpoint accepts valid token")
            else:
                print_error(f"SSE endpoint rejected token: {response.status_code}")

            print("\n3. Testing without token (should fail)...")
            response = await client.get(f"{MCP_BASE_URL}/sse")

            if response.status_code == 401:
                print_success("Correctly rejected request without token (401)")
            else:
                print_error(f"Expected 401, got {response.status_code}")

            print("\n4. Testing with invalid token...")
            response = await client.get(
                f"{MCP_BASE_URL}/sse",
                headers={"Authorization": "Bearer invalid-token-here"},
            )

            if response.status_code == 401:
                print_success("Correctly rejected invalid token (401)")
            else:
                print_error(f"Expected 401, got {response.status_code}")

        except Exception as e:
            print_error(f"Test failed: {e}")


async def test_form_encoded_request():
    """Test token endpoint with form-encoded body."""
    print_test("Form-Encoded Token Request")

    async with httpx.AsyncClient() as client:
        try:
            print("\n1. Testing with application/x-www-form-urlencoded...")
            response = await client.post(
                f"{MCP_BASE_URL}/oauth/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "client_credentials",
                    "client_id": TEST_CLIENT_ID,
                    "client_secret": TEST_CLIENT_SECRET,
                },
            )

            if response.status_code == 200:
                print_success("Form-encoded request works")
                token_data = response.json()
                print(f"   Got token: {token_data['access_token'][:20]}...")
            else:
                print_error(f"Form-encoded request failed: {response.status_code}")
                print(f"   Response: {response.text}")

        except Exception as e:
            print_error(f"Test failed: {e}")


async def main():
    """Run all OAuth tests."""
    print("\n" + "=" * 60)
    print("Monguite MCP Server - OAuth 2.0 Authentication Tests")
    print("=" * 60)

    print("\nConfiguration:")
    print(f"  MCP Base URL: {MCP_BASE_URL}")
    print(f"  Client ID: {TEST_CLIENT_ID}")
    print(f"  Client Secret: {'*' * len(TEST_CLIENT_SECRET)}")

    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MCP_BASE_URL}/health")
            if response.status_code != 200:
                print_error("\n✗ MCP server health check failed")
                print("Make sure the server is running with OAuth enabled:")
                print("  OAUTH_ENABLED=true OAUTH_CLIENT_ID=test-client \\")
                print("    OAUTH_CLIENT_SECRET=test-secret \\")
                print("    OAUTH_JWT_SECRET=your-secret-here \\")
                print("    MCP_TRANSPORT=http uv run python mcp/server.py")
                sys.exit(1)

            health_data = response.json()
            if not health_data.get("oauth_enabled"):
                print_error("\n✗ OAuth is not enabled on the server")
                print("Set OAUTH_ENABLED=true in your environment")
                sys.exit(1)

            print_success("MCP server is running with OAuth enabled\n")

    except httpx.ConnectError:
        print_error("\n✗ Cannot connect to MCP server")
        print("Start the server with: MCP_TRANSPORT=http OAUTH_ENABLED=true uv run python mcp/server.py")
        sys.exit(1)

    # Run tests
    access_token = await test_oauth_token_endpoint()

    if access_token:
        await test_token_authentication(access_token)

    await test_invalid_credentials()
    await test_form_encoded_request()

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
