# Monguite MCP Server

MCP (Model Context Protocol) server for accessing Monguite indigenous land data through AI assistants like Claude.

## Overview

This MCP server exposes the Monguite REST API through the Model Context Protocol, allowing AI assistants like Claude to query indigenous land data.


## Installation

```bash
# Install all dependencies (including MCP server dependencies)
uv sync
```

The MCP server supports **two transport modes**: stdio (default) and HTTP.

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

### Mode 2: HTTP Server (For Custom Clients)

To run as an HTTP server using SSE (Server-Sent Events):

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
- `MCP_PORT`: Port to bind the MCP server (default: `3000`) - HTTP mode only
- `MCP_API_KEY`: API key for authenticating MCP HTTP requests (required for production)

**HTTP Endpoints:**
- `GET /health` - Health check endpoint (returns server and Django API status)
- `GET /sse` - SSE endpoint for MCP protocol communication (requires authentication)
- `POST /messages` - HTTP endpoint for posting messages (requires authentication)

**Authentication:**

The MCP server supports two authentication methods:

1. **OAuth 2.0 Client Credentials Flow** (recommended for production)
2. **Legacy API Key** (for backward compatibility)

### OAuth 2.0 Authentication

OAuth is recommended for production deployments and custom MCP client integrations. It provides:
- Secure token-based authentication
- Token expiration and automatic renewal
- Standard OAuth 2.0 client credentials flow

**Configuration:**

Set the following environment variables:

```bash
OAUTH_ENABLED=true
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret-here
OAUTH_JWT_SECRET=your-jwt-signing-secret-min-32-chars
OAUTH_TOKEN_EXPIRY=3600  # Token expiry in seconds (default: 1 hour)
```

**OAuth Endpoints:**
- `POST /oauth/token` - Token endpoint for client credentials flow

**Getting an Access Token:**

```bash
# Request access token
curl -X POST http://localhost:8001/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "client_credentials",
    "client_id": "your-client-id",
    "client_secret": "your-client-secret"
  }'

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Using the Access Token:**

```bash
# Use the access token in the Authorization header
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     http://localhost:8001/sse
```

**Token Renewal:**

When the token expires (after `expires_in` seconds), request a new token using the same client credentials.

### Legacy API Key Authentication

For backward compatibility, you can use the simple API key authentication:

```bash
MCP_API_KEY=your-api-key-here
```

When `MCP_API_KEY` is set and OAuth is disabled, all requests to `/sse` and `/messages` must include:
```
Authorization: Bearer your-api-key-here
```

**Note:** The `/health` endpoint is always accessible without authentication.


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

## Deployment

### Production Deployment (Heroku, Railway, Render)

The project includes a `Procfile` for deploying both Django and MCP server together:

```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
mcp: MCP_TRANSPORT=http MCP_PORT=3000 python mcp/server.py
```

**Required Environment Variables:**

Copy `.env.production.example` and configure:

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
ALLOWED_HOSTS=your-domain.com

# MCP Server
MCP_TRANSPORT=http
MONGUITE_API_URL=http://localhost:8000

# OAuth Authentication (recommended)
OAUTH_ENABLED=true
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-secure-client-secret
OAUTH_JWT_SECRET=your-jwt-secret-min-32-chars
OAUTH_TOKEN_EXPIRY=3600

# Legacy API Key (alternative to OAuth)
# MCP_API_KEY=your-secure-api-key-here
```

**Deployment Steps:**

1. **Railway/Render:**
   ```bash
   # Push to your git repository
   git push origin main

   # Platform will auto-detect Procfile and deploy both services
   ```

2. **Heroku:**
   ```bash
   heroku create your-app-name
   heroku addons:create heroku-postgresql
   heroku addons:create heroku-redis

   # Set environment variables
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set MCP_TRANSPORT=http
   heroku config:set OAUTH_ENABLED=true
   heroku config:set OAUTH_CLIENT_ID=your-client-id
   heroku config:set OAUTH_CLIENT_SECRET=your-client-secret
   heroku config:set OAUTH_JWT_SECRET=your-jwt-secret

   # Deploy
   git push heroku main

   # Run migrations
   heroku run python manage.py migrate
   ```

3. **Health Check:**
   ```bash
   curl https://your-app.railway.app/health
   ```

### n8n Integration

The MCP server can be integrated with n8n workflows to enable AI-powered data queries during bot conversations.

**Setup Steps:**

1. **Deploy the MCP server** using the deployment instructions above

2. **Configure n8n MCP Client:**

   In your n8n workflow, use the HTTP Request node or a custom MCP client node:

   ```javascript
   // Example: Get OAuth token first
   const tokenEndpoint = 'https://your-app.railway.app/oauth/token';
   const tokenResponse = await fetch(tokenEndpoint, {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       grant_type: 'client_credentials',
       client_id: 'your-client-id',
       client_secret: 'your-client-secret'
     })
   });
   const { access_token } = await tokenResponse.json();

   // Connect to MCP SSE endpoint with OAuth token
   const mcpEndpoint = 'https://your-app.railway.app/sse';
   headers: {
     'Authorization': `Bearer ${access_token}`
   }
   ```

3. **Use MCP Tools in n8n:**

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

# Test SSE endpoint (requires auth)
curl -H "Authorization: Bearer YOUR_API_KEY_HERE" \
     https://your-app.railway.app/sse
```

**Security Notes:**
- Always use HTTPS in production
- Keep `MCP_API_KEY` secret and rotate regularly
- Use environment variables in n8n for API keys
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
heroku logs --tail -a your-app-name
# or
railway logs
```

**Authentication Issues:**

For OAuth:
```bash
# Test OAuth token endpoint
curl -X POST https://your-app.railway.app/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "client_credentials",
    "client_id": "your-client-id",
    "client_secret": "your-client-secret"
  }'

# Verify token works
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
curl -H "Authorization: Bearer $TOKEN" \
     https://your-app.railway.app/health

# Common issues:
# - "invalid_client": Check OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET match
# - "JWT token expired": Request a new token
# - "OAuth not enabled": Set OAUTH_ENABLED=true
```

For Legacy API Key:
```bash
# Verify API key is set
echo $MCP_API_KEY

# Test with correct header
curl -H "Authorization: Bearer $MCP_API_KEY" \
     https://your-app.railway.app/sse
```

**Connection Refused:**
- Ensure both `web` and `mcp` processes are running
- Check that `MONGUITE_API_URL` points to the correct Django server
- Verify firewall/security group settings allow internal communication
