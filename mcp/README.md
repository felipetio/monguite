# Monguite MCP Server

MCP (Model Context Protocol) server for accessing Monguite indigenous land data through AI assistants like Claude.

## Overview

This MCP server exposes the Monguite REST API through the Model Context Protocol, allowing AI assistants like Claude to query indigenous land data.


## Current Setup

```bash
# install mcp dependencies
poetry install --with=mcp

# find the pythpn interpreter path
poetry run whereis python
```

The working configuration uses `server.py`:

```json
{
  "mcpServers": {
    "Monguite": {
      "command": "/path/to/python",
      "args": [
        "/path/to/mcp/server.py"
      ],
      "env": {
        "MONGUITE_API_URL": "http://localhost:8000",
        "MONGUITE_API_TOKEN": ""
      }
    }
  }
}
```


## Testing

Test the MCP server before using it in Claude Desktop:

```bash
# Test with Django server running
poetry run python manage.py runserver &
poetry run python mcp/test.py
```


## Architecture Notes

### MCP Protocol

MCP uses stdio for communication:
- **stdin/stdout**: JSON-RPC protocol messages
- **stderr**: Logging and debugging output

This is why we must:
- Never print to stdout (use stderr for logs)
- Output valid JSON-RPC on stdout only

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
