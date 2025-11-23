#!/bin/bash
# Start both web and mcp processes

# Start MCP server in background
MCP_TRANSPORT="http" MCP_PORT="$MCP_PORT" uv run python mcp/server.py &

# Start web server in foreground
exec gunicorn config.wsgi:application --bind "0.0.0.0:$PORT"
