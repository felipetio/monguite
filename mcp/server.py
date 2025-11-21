#!/usr/bin/env python3
"""
Monguite MCP Server
Exposes the Monguite API for indigenous land data through MCP tools.
"""

import asyncio
import json
import os
import sys
from typing import Any

import httpx
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool

# Environment configuration
API_BASE_URL = os.getenv("MONGUITE_API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("MONGUITE_API_TOKEN", "")
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "3000"))
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")  # stdio or http

# Initialize MCP server
app = Server("monguite-api")


def log(message: str):
    """Log to stderr (stdout is used for MCP protocol)."""
    print(f"[Monguite MCP] {message}", file=sys.stderr, flush=True)


def validate_config():
    """Validate environment configuration at startup."""
    if not API_BASE_URL:
        log("ERROR: MONGUITE_API_URL not set")
        sys.exit(1)

    log("Configuration loaded:")
    log(f"  API URL: {API_BASE_URL}")
    log(f"  API Token: {'Set' if API_TOKEN else 'Not set'}")


async def get_client() -> httpx.AsyncClient:
    """Create an async HTTP client with proper headers and retry logic."""
    headers = {}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"

    # Add retry logic for transient failures
    transport = httpx.AsyncHTTPTransport(retries=3)

    return httpx.AsyncClient(
        base_url=API_BASE_URL, headers=headers, timeout=30.0, transport=transport
    )


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Monguite API tools."""
    tools = [
        Tool(
            name="search_lands",
            description=(
                "Search for indigenous lands in Brazil. Supports filtering by name, "
                "category (DI, PI, RI, TI), state, municipality, biome, and community. "
                "Returns paginated results with land details."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Filter by land name (partial match)",
                    },
                    "category": {
                        "type": "string",
                        "enum": ["DI", "PI", "RI", "TI"],
                        "description": (
                            "Land category: DI (Dominial Indígena), PI (Parque Indígena), "
                            "RI (Reserva Indígena), TI (Terra Indígena)"
                        ),
                    },
                    "state": {
                        "type": "string",
                        "description": "Filter by Brazilian state name",
                    },
                    "state_code": {
                        "type": "string",
                        "description": "Filter by state code (e.g., 'AM', 'PA')",
                    },
                    "municipality": {
                        "type": "string",
                        "description": "Filter by municipality name",
                    },
                    "biome": {
                        "type": "string",
                        "description": "Filter by biome (e.g., 'Amazônia', 'Cerrado', 'Mata Atlântica')",
                    },
                    "community": {
                        "type": "string",
                        "description": "Filter by indigenous community name",
                    },
                    "search": {
                        "type": "string",
                        "description": "General search term across multiple fields",
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number for pagination (default: 1)",
                    },
                    "ordering": {
                        "type": "string",
                        "description": "Field to order by (prefix with '-' for descending)",
                    },
                },
            },
        ),
        Tool(
            name="get_land_details",
            description=(
                "Retrieve detailed information about a specific indigenous land by its UUID. "
                "Returns complete land data including biome, communities, location, and metadata."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "land_id": {
                        "type": "string",
                        "description": "UUID of the land to retrieve",
                    }
                },
                "required": ["land_id"],
            },
        ),
        Tool(
            name="search_communities",
            description=(
                "Search for indigenous communities in Brazil. Supports filtering by name "
                "and number of associated lands. Returns paginated results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Filter by community name (partial match)",
                    },
                    "lands_count_min": {
                        "type": "number",
                        "description": "Minimum number of lands associated with the community",
                    },
                    "lands_count_max": {
                        "type": "number",
                        "description": "Maximum number of lands associated with the community",
                    },
                    "search": {"type": "string", "description": "General search term"},
                    "page": {
                        "type": "integer",
                        "description": "Page number for pagination (default: 1)",
                    },
                    "ordering": {
                        "type": "string",
                        "description": "Field to order by (prefix with '-' for descending)",
                    },
                },
            },
        ),
        Tool(
            name="get_community_details",
            description=(
                "Retrieve detailed information about a specific indigenous community by its UUID. "
                "Returns community data including name and count of associated lands."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "community_id": {
                        "type": "string",
                        "description": "UUID of the community to retrieve",
                    }
                },
                "required": ["community_id"],
            },
        ),
        Tool(
            name="get_api_stats",
            description=(
                "Get summary statistics about the Monguite database. Returns counts of "
                "lands and communities, useful for understanding the dataset scope."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
    ]

    log(f"Registered {len(tools)} tools")
    return tools


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


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls to the Monguite API."""
    log(f"Tool called: {name}")

    async with await get_client() as client:
        try:
            if name == "search_lands":
                params = {k: v for k, v in arguments.items() if v is not None}
                log(f"Searching lands with params: {params}")

                response = await client.get("/api/v1/lands/", params=params)
                response.raise_for_status()
                data = response.json()

                result = {
                    "total_count": data.get("count", 0),
                    "page_results": len(data.get("results", [])),
                    "lands": format_land_results(data.get("results", [])),
                    "next_page": data.get("next") is not None,
                }

                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2, ensure_ascii=False),
                    )
                ]

            elif name == "get_land_details":
                land_id = arguments["land_id"]
                log(f"Fetching land details: {land_id}")

                response = await client.get(f"/api/v1/lands/{land_id}/")
                response.raise_for_status()
                data = response.json()

                return [
                    TextContent(
                        type="text", text=json.dumps(data, indent=2, ensure_ascii=False)
                    )
                ]

            elif name == "search_communities":
                params = {k: v for k, v in arguments.items() if v is not None}
                log(f"Searching communities with params: {params}")

                response = await client.get("/api/v1/communities/", params=params)
                response.raise_for_status()
                data = response.json()

                result = {
                    "total_count": data.get("count", 0),
                    "page_results": len(data.get("results", [])),
                    "communities": data.get("results", []),
                    "next_page": data.get("next") is not None,
                }

                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2, ensure_ascii=False),
                    )
                ]

            elif name == "get_community_details":
                community_id = arguments["community_id"]
                log(f"Fetching community details: {community_id}")

                response = await client.get(f"/api/v1/communities/{community_id}/")
                response.raise_for_status()
                data = response.json()

                return [
                    TextContent(
                        type="text", text=json.dumps(data, indent=2, ensure_ascii=False)
                    )
                ]

            elif name == "get_api_stats":
                log("Fetching API statistics")

                # Get counts from both endpoints
                lands_response = await client.get("/api/v1/lands/", params={"page": 1})
                communities_response = await client.get(
                    "/api/v1/communities/", params={"page": 1}
                )

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

                return [
                    TextContent(
                        type="text",
                        text=json.dumps(stats, indent=2, ensure_ascii=False),
                    )
                ]

            else:
                log(f"Unknown tool: {name}")
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except httpx.HTTPStatusError as e:
            log(f"HTTP error {e.response.status_code}: {e.response.text}")

            # Try to parse error as JSON for better formatting
            error_detail = e.response.text
            try:
                error_json = e.response.json()
                error_detail = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass

            return [
                TextContent(
                    type="text",
                    text=f"API Error {e.response.status_code}:\n{error_detail}",
                )
            ]
        except Exception as e:
            log(f"Unexpected error in {name}: {type(e).__name__}: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_sse(request):
    """Handle SSE connections for MCP protocol."""
    sse = SseServerTransport("/messages")

    async with sse.connect_sse(request.scope, request.receive, request._send) as (
        read_stream,
        write_stream,
    ):
        await app.run(read_stream, write_stream, app.create_initialization_options())

    return Response()


async def handle_messages(request):
    """Handle POST messages from client."""
    sse = SseServerTransport("/messages")

    async with sse.connect_post(request.scope, request.receive, request._send) as (
        read_stream,
        write_stream,
    ):
        await app.run(read_stream, write_stream, app.create_initialization_options())

    return Response()


def create_app():
    """Create the Starlette application."""
    validate_config()

    return Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"]),
        ]
    )


async def run_stdio():
    """Run the MCP server over stdio (for Claude Desktop)."""
    from mcp.server.stdio import stdio_server

    validate_config()
    log("Starting Monguite MCP server (stdio mode)...")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


async def run_http():
    """Run the MCP server over HTTP."""
    import uvicorn

    log(f"Starting Monguite MCP server (HTTP mode) on {MCP_HOST}:{MCP_PORT}...")
    log(f"SSE endpoint: http://{MCP_HOST}:{MCP_PORT}/sse")
    log(f"Messages endpoint: http://{MCP_HOST}:{MCP_PORT}/messages")

    config = uvicorn.Config(
        create_app(), host=MCP_HOST, port=MCP_PORT, log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Run the MCP server in the configured transport mode."""
    if MCP_TRANSPORT.lower() == "http":
        await run_http()
    else:
        await run_stdio()


if __name__ == "__main__":
    asyncio.run(main())
