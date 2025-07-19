#!/usr/bin/env python3
"""
Simple MCP Client

A basic client for testing the MCP server.
"""

import asyncio
import json
import websockets
import requests
from typing import Dict, Any, Optional


class MCPClient:
    """Simple MCP client for testing."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws") + "/ws"
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        response = requests.get(f"{self.base_url}/")
        return response.json()
    
    def get_health(self) -> Dict[str, Any]:
        """Get server health status."""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        response = requests.get(f"{self.base_url}/tools")
        return response.json()
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a tool via REST API."""
        if arguments is None:
            arguments = {}
        
        request_data = {
            "id": "client-request",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = requests.post(f"{self.base_url}/execute", json=request_data)
        return response.json()
    
    async def execute_tool_ws(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a tool via WebSocket."""
        if arguments is None:
            arguments = {}
        
        async with websockets.connect(self.ws_url) as websocket:
            request_data = {
                "id": "ws-client-request",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            await websocket.send(json.dumps(request_data))
            response = await websocket.recv()
            return json.loads(response)


async def main():
    """Test the MCP server."""
    client = MCPClient()
    
    print("=== MCP Server Test ===")
    
    # Test server info
    print("\n1. Server Info:")
    info = client.get_server_info()
    print(json.dumps(info, indent=2))
    
    # Test health
    print("\n2. Health Check:")
    health = client.get_health()
    print(json.dumps(health, indent=2))
    
    # Test tools list
    print("\n3. Available Tools:")
    tools = client.list_tools()
    print(json.dumps(tools, indent=2))
    
    # Test WebSocket connection
    print("\n4. WebSocket Test:")
    try:
        ws_result = await client.execute_tool_ws("get_current_time")
        print("WebSocket response:", json.dumps(ws_result, indent=2))
    except Exception as e:
        print(f"WebSocket error: {e}")
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(main()) 