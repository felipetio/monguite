#!/bin/bash
# Start both web and mcp processes

# Exit immediately if a command exits with a non-zero status
set -e

# Apply database migrations
uv run python manage.py migrate --noinput

# Start MCP server in background
MCP_TRANSPORT="http" MCP_PORT="$MCP_PORT" uv run python mcp/server.py &

# Start web server in foreground
exec gunicorn config.wsgi:application --bind "0.0.0.0:$PORT"
