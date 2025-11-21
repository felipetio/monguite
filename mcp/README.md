# Monguite MCP Server

MCP (Model Context Protocol) server for accessing Monguite indigenous land data through AI assistants like Claude.

## Overview

This MCP server exposes the Monguite REST API through the Model Context Protocol, allowing AI assistants like Claude to query indigenous land data.


## Current Setup

```bash
# install mcp dependencies
poetry install --with=mcp
```

The MCP server supports **two transport modes**: stdio (default) and HTTP.

### Mode 1: stdio (Default - For Claude Desktop)

The server runs in stdio mode by default, which is compatible with Claude Desktop:

```bash
# Find your Python interpreter path
poetry run which python
```

**Claude Desktop Configuration** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "monguite": {
      "command": "/path/to/poetry",
      "args": ["run", "python", "mcp/server.py"],
      "cwd": "/Users/felipe/Projects/monguite",
      "env": {
        "MONGUITE_API_URL": "http://localhost:8000",
        "MONGUITE_API_TOKEN": ""
      }
    }
  }
}
```

Or directly with the Python interpreter:

```json
{
  "mcpServers": {
    "monguite": {
      "command": "/path/to/python",
      "args": ["/Users/felipe/Projects/monguite/mcp/server.py"],
      "env": {
        "MONGUITE_API_URL": "http://localhost:8000",
        "MONGUITE_API_TOKEN": ""
      }
    }
  }
}
```

### Mode 2: HTTP Server (For Custom Clients)

To run as an HTTP server using SSE (Server-Sent Events):

```bash
# Start the MCP server in HTTP mode
MCP_TRANSPORT=http poetry run python mcp/server.py

# Or with custom host/port
MCP_TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8080 poetry run python mcp/server.py
```

**Environment Variables:**
- `MCP_TRANSPORT`: Transport mode - `stdio` (default) or `http`
- `MONGUITE_API_URL`: URL of the Monguite API (default: `http://localhost:8000`)
- `MONGUITE_API_TOKEN`: Optional API token for authentication
- `MCP_HOST`: Host to bind the MCP server (default: `0.0.0.0`) - HTTP mode only
- `MCP_PORT`: Port to bind the MCP server (default: `3000`) - HTTP mode only

**HTTP Endpoints:**
- `GET /sse` - SSE endpoint for MCP protocol communication
- `POST /messages` - HTTP endpoint for posting messages


## Testing

Test the MCP server before using it in Claude Desktop:

```bash
# Test with Django server running
poetry run python manage.py runserver &
poetry run python mcp/test.py
```


## Architecture Notes

### MCP Protocol

The server supports two transport modes:

**stdio mode (default)**:
- **stdin/stdout**: JSON-RPC protocol messages
- **stderr**: Logging and debugging output
- Compatible with Claude Desktop and other stdio-based MCP clients

**HTTP mode**:
- **SSE endpoint** (`/sse`): Establishes a long-lived connection for server-to-client events
- **Messages endpoint** (`/messages`): Accepts POST requests from the client
- **stderr**: Logging and debugging output (visible in server logs)
- Uses **Starlette** ASGI web framework and **Uvicorn** server

## Available Tools

The MCP server exposes 5 tools:

1. **search_lands** - Search indigenous lands with filters (name, category, state, municipality, biome, community)
2. **get_land_details** - Get detailed information about a specific land by UUID
3. **search_communities** - Search communities with filters (name, lands_count)
4. **get_community_details** - Get detailed information about a specific community by UUID
5. **get_api_stats** - Get summary statistics (total lands and communities)


## Common Queries Users Can Make

Once set up, users can ask Claude:

```
"Show me indigenous lands in the Amazon biome"
"How many communities are associated with multiple lands?"
"Find lands in Acre state with category TI"
"What are the most active indigenous communities?"
"Get details about land with ID xyz"
```

## Troubleshooting

See the logs in Claude Desktop:
- macOS: `~/Library/Logs/Claude/mcp*.log`
- Check for JSON parse errors (means something printed to stdout)
- Check for connection errors (API not running)
- Check for import errors (missing dependencies)
