web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
mcp: MCP_TRANSPORT=http MCP_PORT=$MCP_PORT python mcp/server.py
