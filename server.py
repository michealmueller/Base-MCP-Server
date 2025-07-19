"""
MCP Server Implementation

Main server implementation for the Daggerheart MCP server.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
import uvicorn

from .config import MCPConfig
from .tools import ToolRegistry, ToolError, ToolTimeoutError, ToolValidationError


class MCPRequest(BaseModel):
    """MCP request model."""
    id: str
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """MCP response model."""
    id: str
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class MCPNotification(BaseModel):
    """MCP notification model."""
    method: str
    params: Optional[Dict[str, Any]] = None


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.logger = logging.getLogger("connection_manager")
    
    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected WebSockets."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                self.logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)


class MCPServer:
    """Main MCP Server implementation."""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.tool_registry = ToolRegistry()
        self.connection_manager = ConnectionManager()
        self.logger = logging.getLogger("mcp_server")
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="Daggerheart MCP Server",
            description="Production-grade MCP server for Daggerheart AI Agent",
            version="1.0.0",
            docs_url="/docs" if config.debug else None,
            redoc_url="/redoc" if config.debug else None
        )
        
        # Add middleware
        self._setup_middleware()
        
        # Setup routes
        self._setup_routes()
        
        # Register default tools
        self._register_default_tools()
    
    def _setup_middleware(self):
        """Setup FastAPI middleware."""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Trusted host middleware
        if self.config.allowed_origins != ["*"]:
            self.app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=self.config.allowed_origins
            )
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "message": "Daggerheart MCP Server",
                "version": "1.0.0",
                "status": "running"
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "active_connections": len(self.connection_manager.active_connections),
                "registered_tools": len(self.tool_registry.list_tools())
            }
        
        @self.app.get("/tools")
        async def list_tools():
            """List all available tools."""
            tools = []
            for tool_name in self.tool_registry.list_tools():
                metadata = self.tool_registry.get_tool_metadata(tool_name)
                if metadata:
                    tools.append({
                        "name": metadata.name,
                        "description": metadata.description,
                        "version": metadata.version,
                        "tags": metadata.tags,
                        "input_schema": metadata.input_schema,
                        "output_schema": metadata.output_schema
                    })
            return {"tools": tools}
        
        @self.app.post("/execute")
        async def execute_tool(request: MCPRequest):
            """Execute a tool."""
            try:
                if request.method != "tools/call":
                    raise HTTPException(status_code=400, detail="Invalid method")
                
                if not request.params:
                    raise HTTPException(status_code=400, detail="Missing parameters")
                
                tool_name = request.params.get("name")
                tool_params = request.params.get("arguments", {})
                
                if not tool_name:
                    raise HTTPException(status_code=400, detail="Missing tool name")
                
                result = await self.tool_registry.execute_tool(tool_name, **tool_params)
                
                return MCPResponse(
                    id=request.id,
                    result=result
                )
                
            except ToolError as e:
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32603,
                        "message": str(e)
                    }
                )
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32603,
                        "message": "Internal server error"
                    }
                )
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time communication."""
            await self.connection_manager.connect(websocket)
            try:
                while True:
                    # Receive message
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Process message
                    response = await self._process_message(message)
                    
                    # Send response
                    await self.connection_manager.send_personal_message(
                        json.dumps(response.dict()),
                        websocket
                    )
                    
            except WebSocketDisconnect:
                self.connection_manager.disconnect(websocket)
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                self.connection_manager.disconnect(websocket)
    
    def _register_default_tools(self):
        """Register default tools."""
        from .tools import ToolMetadata, BaseTool
        
        # Define the built-in tools
        class GetCurrentTimeTool(BaseTool):
            def __init__(self):
                metadata = ToolMetadata(
                    name="get_current_time",
                    description="Get the current date and time",
                    input_schema={"type": "object", "properties": {}, "required": []},
                    output_schema={"type": "string", "description": "Current timestamp"},
                    tags=["utility", "time"]
                )
                super().__init__(metadata)
            
            async def execute(self, **kwargs):
                import datetime
                return datetime.datetime.now().isoformat()
        
        class SearchWebTool(BaseTool):
            def __init__(self):
                metadata = ToolMetadata(
                    name="search_web",
                    description="Search the web for information",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "max_results": {"type": "integer", "description": "Maximum number of results"}
                        },
                        "required": ["query"]
                    },
                    output_schema={
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Search results"
                    },
                    tags=["web", "search"],
                    timeout=30.0
                )
                super().__init__(metadata)
            
            async def execute(self, query: str, max_results: int = 5):
                # Placeholder implementation
                return [
                    {
                        "title": f"Search result for: {query}",
                        "url": "https://example.com",
                        "snippet": f"Information about {query}"
                    }
                ]
        
        class FileOperationsTool(BaseTool):
            def __init__(self):
                metadata = ToolMetadata(
                    name="file_operations",
                    description="Perform file operations (read, write, list)",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string", "enum": ["read", "write", "list"]},
                            "path": {"type": "string", "description": "File path"},
                            "content": {"type": "string", "description": "File content (for write operation)"}
                        },
                        "required": ["operation", "path"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "data": {"type": "string"},
                            "error": {"type": "string"}
                        }
                    },
                    tags=["file", "system"],
                    timeout=10.0
                )
                super().__init__(metadata)
            
            async def execute(self, operation: str, path: str, content: str = ""):
                import os
                import json
                from pathlib import Path
                
                try:
                    if operation == "read":
                        with open(path, 'r') as f:
                            return {"success": True, "data": f.read(), "error": ""}
                    elif operation == "write":
                        with open(path, 'w') as f:
                            f.write(content)
                        return {"success": True, "data": f"File written to {path}", "error": ""}
                    elif operation == "list":
                        path_obj = Path(path)
                        if path_obj.is_dir():
                            files = [f.name for f in path_obj.iterdir()]
                            return {"success": True, "data": json.dumps(files), "error": ""}
                        else:
                            return {"success": False, "data": "", "error": f"{path} is not a directory"}
                    else:
                        return {"success": False, "data": "", "error": f"Unknown operation: {operation}"}
                except Exception as e:
                    return {"success": False, "data": "", "error": str(e)}
        
        # Register the tools
        self.tool_registry.register(GetCurrentTimeTool())
        self.tool_registry.register(SearchWebTool())
        self.tool_registry.register(FileOperationsTool())
        
        self.logger.info("Default tools registered")
    
    async def _process_message(self, message: Dict[str, Any]) -> MCPResponse:
        """Process incoming MCP message."""
        try:
            request = MCPRequest(**message)
            
            if request.method == "tools/list":
                tools = []
                for tool_name in self.tool_registry.list_tools():
                    metadata = self.tool_registry.get_tool_metadata(tool_name)
                    if metadata:
                        tools.append({
                            "name": metadata.name,
                            "description": metadata.description,
                            "inputSchema": metadata.input_schema
                        })
                
                return MCPResponse(
                    id=request.id,
                    result={"tools": tools}
                )
            
            elif request.method == "tools/call":
                if not request.params:
                    return MCPResponse(
                        id=request.id,
                        error={
                            "code": -32602,
                            "message": "Invalid params"
                        }
                    )
                
                tool_name = request.params.get("name")
                tool_params = request.params.get("arguments", {})
                
                if not tool_name:
                    return MCPResponse(
                        id=request.id,
                        error={
                            "code": -32602,
                            "message": "Missing tool name"
                        }
                    )
                
                result = await self.tool_registry.execute_tool(tool_name, **tool_params)
                
                return MCPResponse(
                    id=request.id,
                    result=result
                )
            
            else:
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {request.method}"
                    }
                )
                
        except ValidationError as e:
            return MCPResponse(
                id=message.get("id", "unknown"),
                error={
                    "code": -32600,
                    "message": f"Invalid request: {e}"
                }
            )
        except ToolError as e:
            return MCPResponse(
                id=message.get("id", "unknown"),
                error={
                    "code": -32603,
                    "message": str(e)
                }
            )
        except Exception as e:
            self.logger.error(f"Unexpected error processing message: {e}")
            return MCPResponse(
                id=message.get("id", "unknown"),
                error={
                    "code": -32603,
                    "message": "Internal server error"
                }
            )
    
    def run(self, host: Optional[str] = None, port: Optional[int] = None):
        """Run the MCP server."""
        host = host or self.config.host
        port = port or self.config.port
        
        self.logger.info(f"Starting MCP server on {host}:{port}")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level=self.config.log_level.lower(),
            access_log=True
        )


def create_server(config: Optional[MCPConfig] = None) -> MCPServer:
    """Create and configure an MCP server."""
    if config is None:
        config = MCPConfig.from_env()
    
    # Validate configuration
    errors = config.validate()
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format=config.log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config.log_file) if config.log_file else logging.NullHandler()
        ]
    )
    
    return MCPServer(config) 