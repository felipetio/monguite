#!/usr/bin/env python3
"""
Test MCP server authentication and endpoints.
Tests the Streamable HTTP transport with Bearer token authentication.

Now uses Django's built-in test client since MCP is served by Django.
"""

import os

from django.test import Client

import pytest

# Django MCP endpoint
MCP_ENDPOINT = "/mcp"
HEALTH_ENDPOINT = "/health"


@pytest.mark.django_db
def test_health_endpoint():
    """Test health check endpoint (no auth required)."""
    print("\n=== Testing Health Endpoint ===")

    client = Client()
    response = client.get(HEALTH_ENDPOINT)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Health endpoint should always be accessible
    assert response.status_code in [200, 503]  # 503 if services are down

    # Check response structure
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "cache" in data["checks"]
    print("Health endpoint accessible and has correct structure")


@pytest.mark.django_db
def test_mcp_without_auth():
    """Test MCP endpoint without authentication (should fail if bearer token is set)."""
    print("\n=== Testing MCP Endpoint Without Auth ===")

    bearer_token = os.getenv("MCP_BEARER_TOKEN", "")

    client = Client()
    response = client.post(
        MCP_ENDPOINT,
        content_type="application/json",
    )
    print(f"Status: {response.status_code}")

    if bearer_token:
        assert response.status_code == 401, "Should reject unauthenticated request"
        print("Correctly rejected unauthenticated request")
    else:
        print("MCP_BEARER_TOKEN not set - endpoint allows unauthenticated access")


@pytest.mark.django_db
def test_mcp_with_invalid_auth():
    """Test MCP endpoint with invalid authentication."""
    print("\n=== Testing MCP Endpoint With Invalid Auth ===")

    bearer_token = os.getenv("MCP_BEARER_TOKEN", "")

    if not bearer_token:
        print("Skipping - MCP_BEARER_TOKEN not set")
        return

    client = Client()
    response = client.post(
        MCP_ENDPOINT,
        content_type="application/json",
        HTTP_AUTHORIZATION="Bearer invalid-token-here",
    )
    print(f"Status: {response.status_code}")

    assert response.status_code == 401, "Should reject invalid bearer token"
    print("Correctly rejected invalid bearer token")


@pytest.mark.django_db
def test_mcp_with_valid_auth():
    """Test MCP endpoint with valid authentication."""
    print("\n=== Testing MCP Endpoint With Valid Auth ===")

    bearer_token = os.getenv("MCP_BEARER_TOKEN", "")

    if not bearer_token:
        print("Skipping - MCP_BEARER_TOKEN not set")
        return

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

    client = Client()
    response = client.post(
        MCP_ENDPOINT,
        data=init_request,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {bearer_token}",
    )
    print(f"Status: {response.status_code}")

    # Should not be 401 (unauthorized)
    assert response.status_code != 401, "Should accept valid bearer token"
    print("Successfully authenticated to MCP endpoint")
