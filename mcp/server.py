#!/usr/bin/env python3
"""
Monguite MCP Server
Exposes the Monguite API for indigenous land data through MCP tools.

Supports two transport modes:
- stdio: For Claude Desktop and local development
- streamable-http: For n8n cloud and production deployments
"""

import json
import os
import sys
from pathlib import Path
from typing import Literal

import httpx
import uvicorn
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file
# Look for .env in the project root (parent of mcp directory)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Environment configuration
API_BASE_URL = os.getenv("MONGUITE_API_URL")
API_TOKEN = os.getenv("MONGUITE_API_TOKEN")
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8001"))
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")  # stdio or http
MCP_BEARER_TOKEN = os.getenv("MCP_BEARER_TOKEN")  # Bearer token for HTTP authentication

# Initialize MCP server
mcp = FastMCP(
    name="monguite-api",
    host=MCP_HOST,
    port=MCP_PORT,
    streamable_http_path="/mcp",
)


def log(message: str):
    """Log to stderr (stdout is used for MCP protocol)."""
    print(f"[Monguite MCP] {message}", file=sys.stderr, flush=True)


def validate_config():
    """Validate environment configuration at startup."""
    if not API_BASE_URL:
        log("ERROR: MONGUITE_API_URL not set")
        sys.exit(1)

    if MCP_TRANSPORT.lower() == "http" and not MCP_BEARER_TOKEN:
        log("WARNING: MCP_BEARER_TOKEN not set - API will be unauthenticated!")

    log("Configuration loaded:")
    log(f"  API URL: {API_BASE_URL}")
    log(f"  API Token: {'Set' if API_TOKEN else 'Not set'}")
    log(f"  MCP Bearer Token: {'Set' if MCP_BEARER_TOKEN else 'Not set'}")


async def get_client() -> httpx.AsyncClient:
    """Create an async HTTP client with proper headers and retry logic."""
    headers = {}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"

    # Add retry logic for transient failures
    transport = httpx.AsyncHTTPTransport(retries=3)

    return httpx.AsyncClient(base_url=API_BASE_URL, headers=headers, timeout=30.0, transport=transport)


def format_land_results(results: list[dict]) -> list[dict]:
    """Format land results for better readability."""
    formatted = []
    for land in results:
        formatted.append(
            {
                "id": land["id"],
                "name": land["name"],
                "category": land["category_display"],
                "location": land["location"],
                "biome": land["biome"]["name"] if land.get("biome") else None,
                "communities_count": land["communities_count"],
                "communities": [c["name"] for c in land.get("communities", [])],
            }
        )
    return formatted


@mcp.tool()
async def search_lands(
    name: str | None = None,
    category: Literal["DI", "PI", "RI", "TI"] | None = None,
    state: str | None = None,
    state_code: str | None = None,
    municipality: str | None = None,
    biome: str | None = None,
    community: str | None = None,
    search: str | None = None,
    page: int | None = None,
    ordering: str | None = None,
) -> str:
    """Search for indigenous lands in Brazil.

    Supports filtering by name, category, state, municipality, biome, and community.
    Returns paginated results with land details.

    Args:
        name: Filter by land name (partial match)
        category: Land category - DI (Dominial Indígena), PI (Parque Indígena), RI (Reserva Indígena), TI (Terra Indígena)
        state: Filter by Brazilian state name
        state_code: Filter by state code (e.g., 'AM', 'PA')
        municipality: Filter by municipality name
        biome: Filter by biome (e.g., 'Amazônia', 'Cerrado', 'Mata Atlântica')
        community: Filter by indigenous community name
        search: General search term across multiple fields
        page: Page number for pagination (default: 1)
        ordering: Field to order by (prefix with '-' for descending)
    """
    log("Tool called: search_lands")

    params = {}
    if name is not None:
        params["name"] = name
    if category is not None:
        params["category"] = category
    if state is not None:
        params["state"] = state
    if state_code is not None:
        params["state_code"] = state_code
    if municipality is not None:
        params["municipality"] = municipality
    if biome is not None:
        params["biome"] = biome
    if community is not None:
        params["community"] = community
    if search is not None:
        params["search"] = search
    if page is not None:
        params["page"] = page
    if ordering is not None:
        params["ordering"] = ordering

    log(f"Searching lands with params: {params}")

    async with await get_client() as client:
        try:
            response = await client.get("/api/v1/lands/", params=params)
            response.raise_for_status()
            data = response.json()

            result = {
                "total_count": data.get("count", 0),
                "page_results": len(data.get("results", [])),
                "lands": format_land_results(data.get("results", [])),
                "next_page": data.get("next") is not None,
            }

            return json.dumps(result, indent=2, ensure_ascii=False)

        except httpx.HTTPStatusError as e:
            log(f"HTTP error {e.response.status_code}: {e.response.text}")
            return f"API Error {e.response.status_code}: {e.response.text}"
        except Exception as e:
            log(f"Unexpected error: {type(e).__name__}: {e}")
            return f"Error: {str(e)}"


@mcp.tool()
async def get_land_details(land_id: str) -> str:
    """Retrieve detailed information about a specific indigenous land by its UUID.

    Returns complete land data including biome, communities, location, and metadata.

    Args:
        land_id: UUID of the land to retrieve
    """
    log(f"Tool called: get_land_details({land_id})")

    async with await get_client() as client:
        try:
            response = await client.get(f"/api/v1/lands/{land_id}/")
            response.raise_for_status()
            data = response.json()

            return json.dumps(data, indent=2, ensure_ascii=False)

        except httpx.HTTPStatusError as e:
            log(f"HTTP error {e.response.status_code}: {e.response.text}")
            return f"API Error {e.response.status_code}: {e.response.text}"
        except Exception as e:
            log(f"Unexpected error: {type(e).__name__}: {e}")
            return f"Error: {str(e)}"


@mcp.tool()
async def search_communities(
    name: str | None = None,
    lands_count_min: int | None = None,
    lands_count_max: int | None = None,
    search: str | None = None,
    page: int | None = None,
    ordering: str | None = None,
) -> str:
    """Search for indigenous communities in Brazil.

    Supports filtering by name and number of associated lands.
    Returns paginated results.

    Args:
        name: Filter by community name (partial match)
        lands_count_min: Minimum number of lands associated with the community
        lands_count_max: Maximum number of lands associated with the community
        search: General search term
        page: Page number for pagination (default: 1)
        ordering: Field to order by (prefix with '-' for descending)
    """
    log("Tool called: search_communities")

    params = {}
    if name is not None:
        params["name"] = name
    if lands_count_min is not None:
        params["lands_count_min"] = lands_count_min
    if lands_count_max is not None:
        params["lands_count_max"] = lands_count_max
    if search is not None:
        params["search"] = search
    if page is not None:
        params["page"] = page
    if ordering is not None:
        params["ordering"] = ordering

    log(f"Searching communities with params: {params}")

    async with await get_client() as client:
        try:
            response = await client.get("/api/v1/communities/", params=params)
            response.raise_for_status()
            data = response.json()

            result = {
                "total_count": data.get("count", 0),
                "page_results": len(data.get("results", [])),
                "communities": data.get("results", []),
                "next_page": data.get("next") is not None,
            }

            return json.dumps(result, indent=2, ensure_ascii=False)

        except httpx.HTTPStatusError as e:
            log(f"HTTP error {e.response.status_code}: {e.response.text}")
            return f"API Error {e.response.status_code}: {e.response.text}"
        except Exception as e:
            log(f"Unexpected error: {type(e).__name__}: {e}")
            return f"Error: {str(e)}"


@mcp.tool()
async def get_community_details(community_id: str) -> str:
    """Retrieve detailed information about a specific indigenous community by its UUID.

    Returns community data including name and count of associated lands.

    Args:
        community_id: UUID of the community to retrieve
    """
    log(f"Tool called: get_community_details({community_id})")

    async with await get_client() as client:
        try:
            response = await client.get(f"/api/v1/communities/{community_id}/")
            response.raise_for_status()
            data = response.json()

            return json.dumps(data, indent=2, ensure_ascii=False)

        except httpx.HTTPStatusError as e:
            log(f"HTTP error {e.response.status_code}: {e.response.text}")
            return f"API Error {e.response.status_code}: {e.response.text}"
        except Exception as e:
            log(f"Unexpected error: {type(e).__name__}: {e}")
            return f"Error: {str(e)}"


@mcp.tool()
async def get_api_stats() -> str:
    """Get summary statistics about the Monguite database.

    Returns counts of lands and communities, useful for understanding the dataset scope.
    """
    log("Tool called: get_api_stats")

    async with await get_client() as client:
        try:
            # Get counts from both endpoints
            lands_response = await client.get("/api/v1/lands/", params={"page": 1})
            communities_response = await client.get("/api/v1/communities/", params={"page": 1})

            lands_response.raise_for_status()
            communities_response.raise_for_status()

            lands_data = lands_response.json()
            communities_data = communities_response.json()

            stats = {
                "total_lands": lands_data.get("count", 0),
                "total_communities": communities_data.get("count", 0),
                "api_base_url": API_BASE_URL,
                "api_status": "connected",
            }

            return json.dumps(stats, indent=2, ensure_ascii=False)

        except httpx.HTTPStatusError as e:
            log(f"HTTP error {e.response.status_code}: {e.response.text}")
            return f"API Error {e.response.status_code}: {e.response.text}"
        except Exception as e:
            log(f"Unexpected error: {type(e).__name__}: {e}")
            return f"Error: {str(e)}"


# HTTP mode middleware and endpoints


class BearerTokenMiddleware(BaseHTTPMiddleware):
    """Middleware to validate Bearer token authentication."""

    async def dispatch(self, request: Request, call_next):
        # Skip auth for health endpoint
        if request.url.path == "/health":
            return await call_next(request)

        # Allow unauthenticated access in development mode (no token configured)
        if not MCP_BEARER_TOKEN:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                {"error": "Unauthorized", "message": "Missing Bearer token"},
                status_code=401,
            )

        token = auth_header[7:]  # Remove "Bearer " prefix
        if token != MCP_BEARER_TOKEN:
            return JSONResponse(
                {"error": "Unauthorized", "message": "Invalid Bearer token"},
                status_code=401,
            )

        return await call_next(request)


async def handle_health(request: Request):
    """Health check endpoint."""
    # Test Django API connectivity
    api_status = "disconnected"
    api_error = None

    try:
        async with await get_client() as client:
            response = await client.get("/api/v1/lands/", params={"page": 1})
            response.raise_for_status()
            api_status = "connected"
    except Exception as e:
        api_error = str(e)

    health_data = {
        "status": "healthy" if api_status == "connected" else "degraded",
        "mcp_server": "running",
        "django_api": api_status,
        "api_url": API_BASE_URL,
    }

    if api_error:
        health_data["api_error"] = api_error

    status_code = 200 if api_status == "connected" else 503
    return JSONResponse(health_data, status_code=status_code)


def create_app():
    """Create the Starlette application with Streamable HTTP transport."""
    validate_config()

    # Get the MCP streamable HTTP app
    mcp_app = mcp.streamable_http_app()

    # Create wrapper app with health endpoint and auth middleware
    app = Starlette(
        routes=[
            Route("/health", endpoint=handle_health, methods=["GET"]),
            Mount("/", app=mcp_app),
        ],
        middleware=[
            Middleware(BearerTokenMiddleware),
        ],
    )

    return app


async def run_http():
    """Run the MCP server over HTTP with Streamable HTTP transport."""
    log(f"Starting Monguite MCP server (HTTP mode) on {MCP_HOST}:{MCP_PORT}...")
    log(f"MCP endpoint: http://{MCP_HOST}:{MCP_PORT}/mcp")
    log(f"Health endpoint: http://{MCP_HOST}:{MCP_PORT}/health")

    config = uvicorn.Config(create_app(), host=MCP_HOST, port=MCP_PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


def run_stdio():
    """Run the MCP server over stdio (for Claude Desktop)."""
    validate_config()
    log("Starting Monguite MCP server (stdio mode)...")
    mcp.run(transport="stdio")


def main():
    """Run the MCP server in the configured transport mode."""
    if MCP_TRANSPORT.lower() == "http":
        import asyncio

        asyncio.run(run_http())
    else:
        run_stdio()


if __name__ == "__main__":
    main()
