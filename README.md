# Daggerheart MCP Server

A production-grade Model Context Protocol (MCP) server implementation for the Daggerheart AI Agent system.

## Features

- **FastAPI-based REST API** with WebSocket support
- **Comprehensive tool registry** with caching and error handling
- **Production-ready configuration** with environment variable support
- **Built-in security** with rate limiting and CORS
- **Monitoring and health checks**
- **Extensible tool system** with decorator-based registration
- **Async/await support** for high performance

## Quick Start

### Installation

1. **Install dependencies**:
   ```bash
   pip install -r mcp_server/requirements.txt
   ```

2. **Run the server**:
   ```bash
   python -m mcp_server.main
   ```

3. **Access the API**:
   - REST API: http://localhost:8000
   - WebSocket: ws://localhost:8000/ws
   - Documentation: http://localhost:8000/docs

### Configuration

The server can be configured via environment variables:

```bash
# Server settings
export MCP_HOST=0.0.0.0
export MCP_PORT=8000
export MCP_DEBUG=true

# Logging
export MCP_LOG_LEVEL=INFO
export MCP_LOG_FILE=/var/log/mcp_server.log

# Security
export MCP_API_KEY=your_api_key_here
export MCP_RATE_LIMIT_ENABLED=true
export MCP_RATE_LIMIT_REQUESTS=100
export MCP_RATE_LIMIT_WINDOW=60

# Tool settings
export MCP_MAX_TOOL_EXECUTION_TIME=30
export MCP_TOOL_RETRY_ATTEMPTS=3
export MCP_TOOL_RETRY_DELAY=1.0

# Cache settings
export MCP_CACHE_ENABLED=true
export MCP_CACHE_TTL=3600
export MCP_CACHE_MAX_SIZE=1000
```

## API Endpoints

### REST API

- `GET /` - Server information
- `GET /health` - Health check
- `GET /tools` - List available tools
- `POST /execute` - Execute a tool
- `GET /docs` - API documentation (debug mode)

### WebSocket API

Connect to `ws://localhost:8000/ws` for real-time communication.

#### Request Format

```json
{
  "id": "request-1",
  "method": "tools/call",
  "params": {
    "name": "get_current_time",
    "arguments": {}
  }
}
```

#### Response Format

```json
{
  "id": "request-1",
  "result": "2024-01-15T14:30:25.123456",
  "error": null
}
```

## Tool System

### Creating Tools

Tools can be created using the `@tool` decorator:

```python
from mcp_server.tools import tool, ToolMetadata

@tool(ToolMetadata(
    name="my_tool",
    description="My custom tool",
    input_schema={
        "type": "object",
        "properties": {
            "param1": {"type": "string"}
        },
        "required": ["param1"]
    },
    output_schema={"type": "string"},
    tags=["custom"],
    timeout=30.0
))
async def my_tool(param1: str) -> str:
    """My custom tool implementation."""
    return f"Processed: {param1}"
```

### Built-in Tools

- `get_current_time` - Get current timestamp
- `search_web` - Search the web for information
- `file_operations` - Read, write, and list files

## Development

### Project Structure

```
mcp_server/
├── __init__.py          # Package initialization
├── config.py            # Configuration management
├── tools.py             # Tool registry and base classes
├── server.py            # Main server implementation
├── main.py              # Command-line entry point
├── requirements.txt     # Dependencies
└── README.md           # This file
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest mcp_server/tests/ -v

# Run with coverage
pytest mcp_server/tests/ --cov=mcp_server --cov-report=html
```

### Code Quality

```bash
# Format code
black mcp_server/

# Lint code
flake8 mcp_server/

# Type checking
mypy mcp_server/
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY mcp_server/requirements.txt .
RUN pip install -r requirements.txt

COPY mcp_server/ ./mcp_server/

EXPOSE 8000

CMD ["python", "-m", "mcp_server.main", "--host", "0.0.0.0"]
```

### Systemd Service

Create `/etc/systemd/system/mcp-server.service`:

```ini
[Unit]
Description=Daggerheart MCP Server
After=network.target

[Service]
Type=simple
User=mcp
WorkingDirectory=/opt/mcp-server
Environment=PATH=/opt/mcp-server/venv/bin
ExecStart=/opt/mcp-server/venv/bin/python -m mcp_server.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Environment Variables

For production deployment, set these environment variables:

```bash
# Production settings
export MCP_HOST=0.0.0.0
export MCP_PORT=8000
export MCP_DEBUG=false
export MCP_LOG_LEVEL=INFO
export MCP_LOG_FILE=/var/log/mcp-server.log

# Security
export MCP_API_KEY=your_secure_api_key
export MCP_RATE_LIMIT_ENABLED=true
export MCP_RATE_LIMIT_REQUESTS=1000
export MCP_RATE_LIMIT_WINDOW=60

# Performance
export MCP_CACHE_ENABLED=true
export MCP_CACHE_TTL=3600
export MCP_MAX_TOOL_EXECUTION_TIME=60
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": 1705323025.123456,
  "active_connections": 2,
  "registered_tools": 5
}
```

### Metrics

The server exposes metrics at `/metrics` (when enabled):

```bash
curl http://localhost:8000/metrics
```

## Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Check what's using the port
   lsof -i :8000
   
   # Use a different port
   python -m mcp_server.main --port 9000
   ```

2. **Permission denied**:
   ```bash
   # Check file permissions
   ls -la mcp_server/
   
   # Fix permissions
   chmod +x mcp_server/main.py
   ```

3. **Import errors**:
   ```bash
   # Install dependencies
   pip install -r mcp_server/requirements.txt
   
   # Check Python path
   python -c "import mcp_server"
   ```

### Logs

Check logs for detailed error information:

```bash
# View logs
tail -f /var/log/mcp-server.log

# Filter by level
grep "ERROR" /var/log/mcp-server.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License. 