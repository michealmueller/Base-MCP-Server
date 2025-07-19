"""
MCP Server Configuration

Configuration management for the Daggerheart MCP server.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path


@dataclass
class MCPConfig:
    """Configuration for the MCP Server."""
    
    # Server settings
    host: str = "localhost"
    port: int = 8000
    debug: bool = True
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Security settings
    api_key: Optional[str] = None
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # Tool settings
    max_tool_execution_time: int = 30  # seconds
    tool_retry_attempts: int = 3
    tool_retry_delay: float = 1.0  # seconds
    
    # Database settings (for persistent storage)
    database_url: Optional[str] = None
    database_pool_size: int = 10
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl: int = 3600  # seconds
    cache_max_size: int = 1000
    
    # Monitoring settings
    metrics_enabled: bool = True
    health_check_interval: int = 30  # seconds
    
    @classmethod
    def from_env(cls) -> "MCPConfig":
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("MCP_HOST", "localhost"),
            port=int(os.getenv("MCP_PORT", "8000")),
            debug=os.getenv("MCP_DEBUG", "false").lower() == "true",
            log_level=os.getenv("MCP_LOG_LEVEL", "INFO"),
            log_file=os.getenv("MCP_LOG_FILE"),
            api_key=os.getenv("MCP_API_KEY"),
            database_url=os.getenv("MCP_DATABASE_URL"),
            rate_limit_enabled=os.getenv("MCP_RATE_LIMIT_ENABLED", "true").lower() == "true",
            rate_limit_requests=int(os.getenv("MCP_RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window=int(os.getenv("MCP_RATE_LIMIT_WINDOW", "60")),
            max_tool_execution_time=int(os.getenv("MCP_MAX_TOOL_EXECUTION_TIME", "30")),
            tool_retry_attempts=int(os.getenv("MCP_TOOL_RETRY_ATTEMPTS", "3")),
            tool_retry_delay=float(os.getenv("MCP_TOOL_RETRY_DELAY", "1.0")),
            cache_enabled=os.getenv("MCP_CACHE_ENABLED", "true").lower() == "true",
            cache_ttl=int(os.getenv("MCP_CACHE_TTL", "3600")),
            cache_max_size=int(os.getenv("MCP_CACHE_MAX_SIZE", "1000")),
            metrics_enabled=os.getenv("MCP_METRICS_ENABLED", "true").lower() == "true",
            health_check_interval=int(os.getenv("MCP_HEALTH_CHECK_INTERVAL", "30")),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "host": self.host,
            "port": self.port,
            "debug": self.debug,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "api_key": self.api_key,
            "allowed_origins": self.allowed_origins,
            "rate_limit_enabled": self.rate_limit_enabled,
            "rate_limit_requests": self.rate_limit_requests,
            "rate_limit_window": self.rate_limit_window,
            "max_tool_execution_time": self.max_tool_execution_time,
            "tool_retry_attempts": self.tool_retry_attempts,
            "tool_retry_delay": self.tool_retry_delay,
            "database_url": self.database_url,
            "database_pool_size": self.database_pool_size,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "cache_max_size": self.cache_max_size,
            "metrics_enabled": self.metrics_enabled,
            "health_check_interval": self.health_check_interval,
        }
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if self.port < 1 or self.port > 65535:
            errors.append("Port must be between 1 and 65535")
        
        if self.rate_limit_requests < 1:
            errors.append("Rate limit requests must be at least 1")
        
        if self.rate_limit_window < 1:
            errors.append("Rate limit window must be at least 1 second")
        
        if self.max_tool_execution_time < 1:
            errors.append("Max tool execution time must be at least 1 second")
        
        if self.tool_retry_attempts < 0:
            errors.append("Tool retry attempts must be non-negative")
        
        if self.tool_retry_delay < 0:
            errors.append("Tool retry delay must be non-negative")
        
        if self.cache_ttl < 1:
            errors.append("Cache TTL must be at least 1 second")
        
        if self.cache_max_size < 1:
            errors.append("Cache max size must be at least 1")
        
        if self.health_check_interval < 1:
            errors.append("Health check interval must be at least 1 second")
        
        return errors 