web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
mcp: MCP_TRANSPORT=http MCP_PORT=3000 python mcp/server.py
