#!/usr/bin/env python3
"""
MCP Server Main Entry Point

Production-grade MCP server for Daggerheart AI Agent.
"""

import argparse
import logging
import sys
from pathlib import Path

# Handle imports for both module and direct execution
try:
    from .config import MCPConfig
    from .server import create_server
except ImportError:
    # When running directly from mcp_server directory
    from config import MCPConfig
    from server import create_server


def setup_logging(config: MCPConfig):
    """Setup logging configuration."""
    handlers = [logging.StreamHandler()]
    
    if config.log_file:
        log_path = Path(config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(config.log_file))
    
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format=config.log_format,
        handlers=handlers
    )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Daggerheart MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m mcp_server.main                    # Run with default settings
  python -m mcp_server.main --host 0.0.0.0    # Bind to all interfaces
  python -m mcp_server.main --port 9000       # Use custom port
  python -m mcp_server.main --debug            # Enable debug mode
        """
    )
    
    parser.add_argument(
        "--host",
        default=None,
        help="Host to bind to (default: from config or localhost)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind to (default: from config or 8000)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    
    parser.add_argument(
        "--log-file",
        help="Log file path"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Load configuration
        config = MCPConfig.from_env()
        
        # Override with command line arguments
        if args.host:
            config.host = args.host
        if args.port:
            config.port = args.port
        if args.debug:
            config.debug = True
        if args.log_level:
            config.log_level = args.log_level
        if args.log_file:
            config.log_file = args.log_file
        
        # Setup logging
        setup_logging(config)
        
        # Validate configuration
        errors = config.validate()
        if errors:
            print("Configuration errors:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            sys.exit(1)
        
        # Create and run server
        server = create_server(config)
        
        print(f"Starting Daggerheart MCP Server...")
        print(f"  Host: {config.host}")
        print(f"  Port: {config.port}")
        print(f"  Debug: {config.debug}")
        print(f"  Log Level: {config.log_level}")
        if config.log_file:
            print(f"  Log File: {config.log_file}")
        print()
        
        server.run()
        
    except KeyboardInterrupt:
        print("\nShutting down MCP server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting MCP server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 