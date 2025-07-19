"""
Daggerheart MCP Server

A production-grade Model Context Protocol (MCP) server implementation
for the Daggerheart AI Agent system.
"""

__version__ = "1.0.0"
__author__ = "Daggerheart Team"
__description__ = "Production-grade MCP server for Daggerheart AI Agent"

from .server import MCPServer
from .tools import ToolRegistry
from .config import MCPConfig

__all__ = ["MCPServer", "ToolRegistry", "MCPConfig"] 