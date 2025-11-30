# Monguite MCP Server

MCP (Model Context Protocol) server for accessing Monguite indigenous land data through AI assistants like Claude.

## Overview

This MCP server exposes the Monguite REST API through the Model Context Protocol, allowing AI assistants like Claude to query indigenous land data.


## Installation

```bash
# Install all dependencies (including MCP server dependencies)
uv sync
```

The MCP server supports **two transport modes**: stdio (default) and Streamable HTTP.

### Mode 1: stdio (Default - For Claude Desktop)

The server runs in stdio mode by default, which is compatible with Claude Desktop:

```bash
# Find your Python interpreter path
uv run which python
```

**Claude Desktop Configuration** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "monguite": {
      "command": "uv",
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

### Mode 2: HTTP Server (Streamable HTTP - For n8n Cloud)

To run as an HTTP server using Streamable HTTP transport:

```bash
# Start the MCP server in HTTP mode
MCP_TRANSPORT=http uv run python mcp/server.py

# Or with custom host/port
MCP_TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8080 uv run python mcp/server.py
```

**Environment Variables:**
- `MCP_TRANSPORT`: Transport mode - `stdio` (default) or `http`
- `MONGUITE_API_URL`: URL of the Monguite API (default: `http://localhost:8000`)
- `MONGUITE_API_TOKEN`: Optional API token for Django API authentication
- `MCP_HOST`: Host to bind the MCP server (default: `0.0.0.0`) - HTTP mode only
- `MCP_PORT`: Port to bind the MCP server (default: `8001`) - HTTP mode only
- `MCP_BEARER_TOKEN`: Bearer token for authenticating MCP HTTP requests (required for production)

**HTTP Endpoints:**
- `GET /health` - Health check endpoint (returns server and Django API status)
- `POST /mcp` - Streamable HTTP endpoint for MCP protocol (requires authentication)

**Authentication:**

When `MCP_BEARER_TOKEN` is set, all requests to `/mcp` must include:
```
Authorization: Bearer your-bearer-token-here
```

The `/health` endpoint is always accessible without authentication.


## Testing

Test the MCP server before using it in Claude Desktop:

```bash
# Test with Django server running
uv run python manage.py runserver &
uv run python mcp/test.py
```


## Architecture Notes

### MCP Protocol

The server supports two transport modes:

**stdio mode (default)**:
- **stdin/stdout**: JSON-RPC protocol messages
- **stderr**: Logging and debugging output
- Compatible with Claude Desktop and other stdio-based MCP clients

**HTTP mode (Streamable HTTP)**:
- **Single endpoint** (`/mcp`): Handles all MCP protocol messages via POST
- Uses HTTP POST for requests, can respond with JSON or SSE stream
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

## Deployment

### Production Deployment (Railway, Render, etc.)

**Required Environment Variables:**

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
ALLOWED_HOSTS=your-domain.com

# MCP Server
MCP_TRANSPORT=http
MCP_BEARER_TOKEN=your-secure-bearer-token-here
MONGUITE_API_URL=http://localhost:8000
```

**Deployment Steps:**

1. **Railway/Render:**
   ```bash
   # Push to your git repository
   git push origin main

   # Platform will auto-detect and deploy
   ```

2. **Health Check:**
   ```bash
   curl https://your-app.railway.app/health
   ```

### n8n Cloud Integration

The MCP server is designed to work with n8n cloud using Streamable HTTP transport.

**n8n MCP Client Configuration:**

```
URL: https://your-app.railway.app/mcp
Method: POST
Headers:
  Authorization: Bearer your-bearer-token
  Content-Type: application/json
  Accept: application/json, text/event-stream
```

**Use MCP Tools in n8n:**

The MCP server exposes 5 tools that can be called from n8n workflows:
- `search_lands` - Search indigenous lands
- `get_land_details` - Get land details
- `search_communities` - Search communities
- `get_community_details` - Get community details
- `get_api_stats` - Get database statistics

**Example n8n Workflow:**

```
User Message → AI Agent → MCP Tool Call → Monguite API → Response
```

**Testing the Connection:**

```bash
# Test health endpoint (no auth required)
curl https://your-app.railway.app/health

# Test MCP endpoint (requires auth)
# Replace <your-token> with your actual MCP_BEARER_TOKEN value
curl -X POST \
     -H "Authorization: Bearer <your-token>" \
     -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     https://your-app.railway.app/mcp
```

**Security Notes:**
- Always use HTTPS in production
- Keep `MCP_BEARER_TOKEN` secret and rotate regularly
- Use environment variables in n8n for tokens
- Monitor the `/health` endpoint for service status

## Troubleshooting

### Local Development

See the logs in Claude Desktop:
- macOS: `~/Library/Logs/Claude/mcp*.log`
- Check for JSON parse errors (means something printed to stdout)
- Check for connection errors (API not running)
- Check for import errors (missing dependencies)

### Production Deployment

**Health Check Failing:**
```bash
# Check if Django API is accessible
curl http://localhost:8000/api/v1/lands/

# Check MCP server logs
railway logs
```

**Authentication Issues:**
```bash
# Verify bearer token is set
echo $MCP_BEARER_TOKEN

# Test with correct header (replace <your-token>)
curl -X POST \
     -H "Authorization: Bearer <your-token>" \
     https://your-app.railway.app/mcp
```

**Connection Refused:**
- Ensure the MCP server process is running
- Check that `MONGUITE_API_URL` points to the correct Django server
- Verify firewall/security group settings allow internal communication
