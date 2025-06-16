#!/usr/bin/env python3
"""Direct MCP server runner"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Also ensure we can import from app module
if __name__ == "__main__":
    try:
        # Import and run the MCP server
        from app.mcp_server import mcp
        mcp.run()
    except ImportError as e:
        print(f"Import error: {e}")
        print(f"Python executable: {sys.executable}")
        print(f"Python path: {sys.path}")
        raise