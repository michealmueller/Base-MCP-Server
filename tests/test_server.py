"""
Test suite for the MCP server.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch

from mcp_server.config import MCPConfig
from mcp_server.server import MCPServer, create_server
from mcp_server.tools import ToolRegistry, ToolMetadata, BaseTool


class TestTool(BaseTool):
    """Test tool for testing."""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}, "required": []},
            output_schema={"type": "string"}
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs):
        return "test_result"


@pytest.fixture
def config():
    """Create a test configuration."""
    return MCPConfig(
        host="localhost",
        port=8000,
        debug=True,
        log_level="DEBUG"
    )


@pytest.fixture
def server(config):
    """Create a test server."""
    return MCPServer(config)


@pytest.fixture
def tool_registry():
    """Create a test tool registry."""
    registry = ToolRegistry()
    registry.register(TestTool())
    return registry


class TestMCPConfig:
    """Test configuration management."""
    
    def test_config_creation(self):
        """Test config creation."""
        config = MCPConfig()
        assert config.host == "localhost"
        assert config.port == 8000
        assert config.debug is False
    
    def test_config_from_env(self, monkeypatch):
        """Test config creation from environment."""
        monkeypatch.setenv("MCP_HOST", "0.0.0.0")
        monkeypatch.setenv("MCP_PORT", "9000")
        monkeypatch.setenv("MCP_DEBUG", "true")
        
        config = MCPConfig.from_env()
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.debug is True
    
    def test_config_validation(self):
        """Test config validation."""
        config = MCPConfig(port=99999)  # Invalid port
        errors = config.validate()
        assert len(errors) > 0
        assert "Port must be between 1 and 65535" in errors
    
    def test_config_to_dict(self):
        """Test config serialization."""
        config = MCPConfig()
        config_dict = config.to_dict()
        assert "host" in config_dict
        assert "port" in config_dict
        assert config_dict["host"] == "localhost"


class TestToolRegistry:
    """Test tool registry functionality."""
    
    @pytest.mark.asyncio
    async def test_register_tool(self, tool_registry):
        """Test tool registration."""
        assert "test_tool" in tool_registry.list_tools()
        assert tool_registry.get_tool("test_tool") is not None
    
    @pytest.mark.asyncio
    async def test_unregister_tool(self, tool_registry):
        """Test tool unregistration."""
        tool_registry.unregister("test_tool")
        assert "test_tool" not in tool_registry.list_tools()
    
    @pytest.mark.asyncio
    async def test_execute_tool(self, tool_registry):
        """Test tool execution."""
        result = await tool_registry.execute_tool("test_tool")
        assert result == "test_result"
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self, tool_registry):
        """Test executing non-existent tool."""
        with pytest.raises(Exception):
            await tool_registry.execute_tool("nonexistent_tool")
    
    @pytest.mark.asyncio
    async def test_tool_caching(self, tool_registry):
        """Test tool result caching."""
        # First execution
        result1 = await tool_registry.execute_tool("test_tool")
        assert result1 == "test_result"
        
        # Second execution should use cache
        result2 = await tool_registry.execute_tool("test_tool")
        assert result2 == "test_result"
        
        # Clear cache
        tool_registry.clear_cache()
        assert len(tool_registry._cache) == 0


class TestMCPServer:
    """Test MCP server functionality."""
    
    def test_server_creation(self, config):
        """Test server creation."""
        server = MCPServer(config)
        assert server.config == config
        assert server.tool_registry is not None
        assert server.connection_manager is not None
    
    def test_server_middleware_setup(self, server):
        """Test middleware setup."""
        # Check that CORS middleware is added
        cors_middleware = None
        for middleware in server.app.user_middleware:
            if "CORSMiddleware" in str(middleware.cls):
                cors_middleware = middleware
                break
        assert cors_middleware is not None
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, server):
        """Test root endpoint."""
        from fastapi.testclient import TestClient
        
        client = TestClient(server.app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, server):
        """Test health endpoint."""
        from fastapi.testclient import TestClient
        
        client = TestClient(server.app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "active_connections" in data
        assert "registered_tools" in data
    
    @pytest.mark.asyncio
    async def test_tools_endpoint(self, server):
        """Test tools endpoint."""
        from fastapi.testclient import TestClient
        
        client = TestClient(server.app)
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)
    
    @pytest.mark.asyncio
    async def test_execute_endpoint(self, server):
        """Test execute endpoint."""
        from fastapi.testclient import TestClient
        
        client = TestClient(server.app)
        
        # Add a test tool to the registry
        server.tool_registry.register(TestTool())
        
        request_data = {
            "id": "test-1",
            "method": "tools/call",
            "params": {
                "name": "test_tool",
                "arguments": {}
            }
        }
        
        response = client.post("/execute", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-1"
        assert data["result"] == "test_result"
        assert data["error"] is None
    
    @pytest.mark.asyncio
    async def test_execute_endpoint_invalid_method(self, server):
        """Test execute endpoint with invalid method."""
        from fastapi.testclient import TestClient
        
        client = TestClient(server.app)
        
        request_data = {
            "id": "test-1",
            "method": "invalid_method",
            "params": {}
        }
        
        response = client.post("/execute", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid method" in data["detail"]


class TestMessageProcessing:
    """Test message processing functionality."""
    
    @pytest.mark.asyncio
    async def test_process_tools_list_message(self, server):
        """Test processing tools/list message."""
        message = {
            "id": "test-1",
            "method": "tools/list"
        }
        
        response = await server._process_message(message)
        
        assert response.id == "test-1"
        assert response.result is not None
        assert "tools" in response.result
        assert response.error is None
    
    @pytest.mark.asyncio
    async def test_process_tools_call_message(self, server):
        """Test processing tools/call message."""
        # Add a test tool
        server.tool_registry.register(TestTool())
        
        message = {
            "id": "test-1",
            "method": "tools/call",
            "params": {
                "name": "test_tool",
                "arguments": {}
            }
        }
        
        response = await server._process_message(message)
        
        assert response.id == "test-1"
        assert response.result == "test_result"
        assert response.error is None
    
    @pytest.mark.asyncio
    async def test_process_invalid_message(self, server):
        """Test processing invalid message."""
        message = {
            "id": "test-1",
            "method": "invalid_method"
        }
        
        response = await server._process_message(message)
        
        assert response.id == "test-1"
        assert response.result is None
        assert response.error is not None
        assert response.error["code"] == -32601


def test_create_server():
    """Test server creation function."""
    server = create_server()
    assert isinstance(server, MCPServer)
    assert server.config is not None


if __name__ == "__main__":
    pytest.main([__file__]) 