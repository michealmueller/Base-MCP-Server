"""
MCP Server Tools

Tool registry and management for the Daggerheart MCP server.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union, Type
from functools import wraps
import json
import hashlib


@dataclass
class ToolMetadata:
    """Metadata for a tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    timeout: Optional[float] = None
    retry_attempts: int = 3
    cache_enabled: bool = True


class ToolError(Exception):
    """Base exception for tool errors."""
    pass


class ToolTimeoutError(ToolError):
    """Exception raised when tool execution times out."""
    pass


class ToolValidationError(ToolError):
    """Exception raised when tool input validation fails."""
    pass


class BaseTool(ABC):
    """Base class for all tools."""
    
    def __init__(self, metadata: ToolMetadata):
        self.metadata = metadata
        self.logger = logging.getLogger(f"tool.{metadata.name}")
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""
        pass
    
    def validate_input(self, **kwargs) -> bool:
        """Validate tool input against schema."""
        # Basic validation - can be overridden by subclasses
        required_fields = self.metadata.input_schema.get("required", [])
        for field in required_fields:
            if field not in kwargs:
                raise ToolValidationError(f"Required field '{field}' is missing")
        return True
    
    def get_cache_key(self, **kwargs) -> str:
        """Generate cache key for tool execution."""
        # Create a deterministic cache key based on tool name and parameters
        cache_data = {
            "tool": self.metadata.name,
            "version": self.metadata.version,
            "params": sorted(kwargs.items())
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()


class ToolRegistry:
    """Registry for managing tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._cache: Dict[str, Any] = {}
        self.logger = logging.getLogger("tool_registry")
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        if tool.metadata.name in self._tools:
            self.logger.warning(f"Tool '{tool.metadata.name}' already registered, overwriting")
        
        self._tools[tool.metadata.name] = tool
        self.logger.info(f"Registered tool: {tool.metadata.name}")
    
    def unregister(self, tool_name: str) -> None:
        """Unregister a tool."""
        if tool_name in self._tools:
            del self._tools[tool_name]
            self.logger.info(f"Unregistered tool: {tool_name}")
        else:
            self.logger.warning(f"Tool '{tool_name}' not found in registry")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """Get metadata for a tool."""
        tool = self.get_tool(tool_name)
        return tool.metadata if tool else None
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool with caching and error handling."""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ToolError(f"Tool '{tool_name}' not found")
        
        # Validate input
        tool.validate_input(**kwargs)
        
        # Check cache if enabled
        if tool.metadata.cache_enabled:
            cache_key = tool.get_cache_key(**kwargs)
            if cache_key in self._cache:
                self.logger.debug(f"Cache hit for tool '{tool_name}'")
                return self._cache[cache_key]
        
        # Execute tool with timeout
        try:
            if tool.metadata.timeout:
                result = await asyncio.wait_for(
                    tool.execute(**kwargs),
                    timeout=tool.metadata.timeout
                )
            else:
                result = await tool.execute(**kwargs)
            
            # Cache result if enabled
            if tool.metadata.cache_enabled:
                cache_key = tool.get_cache_key(**kwargs)
                self._cache[cache_key] = result
            
            return result
            
        except asyncio.TimeoutError:
            raise ToolTimeoutError(f"Tool '{tool_name}' execution timed out")
        except Exception as e:
            self.logger.error(f"Error executing tool '{tool_name}': {e}")
            raise ToolError(f"Tool execution failed: {e}")
    
    def clear_cache(self) -> None:
        """Clear the tool cache."""
        self._cache.clear()
        self.logger.info("Tool cache cleared")


def tool(metadata: ToolMetadata):
    """Decorator to register a function as a tool."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(**kwargs):
            return await func(**kwargs)
        
        # Create a tool instance
        class FunctionTool(BaseTool):
            async def execute(self, **kwargs):
                return await wrapper(**kwargs)
        
        # Register the tool
        registry = ToolRegistry()
        tool_instance = FunctionTool(metadata)
        registry.register(tool_instance)
        
        return wrapper
    return decorator


# Example tools
@tool(ToolMetadata(
    name="get_current_time",
    description="Get the current date and time",
    input_schema={"type": "object", "properties": {}, "required": []},
    output_schema={"type": "string", "description": "Current timestamp"},
    tags=["utility", "time"]
))
async def get_current_time() -> str:
    """Get current timestamp."""
    import datetime
    return datetime.datetime.now().isoformat()


@tool(ToolMetadata(
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
))
async def search_web(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search the web for information."""
    # Placeholder implementation
    return [
        {
            "title": f"Search result for: {query}",
            "url": "https://example.com",
            "snippet": f"Information about {query}"
        }
    ]


@tool(ToolMetadata(
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
))
async def file_operations(operation: str, path: str, content: str = "") -> Dict[str, Any]:
    """Perform file operations."""
    import os
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