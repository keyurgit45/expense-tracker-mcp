"""
MCP Server for Expense Tracker - Main entry point
"""
import sys
from pathlib import Path

# Add the project root to Python path to ensure imports work
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server.fastmcp import FastMCP

# Import registration functions
from app.servers.mcp.tools import register_tools
from app.servers.mcp.resources import register_resources
from app.servers.mcp.prompts import register_prompts

# Initialize MCP server
mcp = FastMCP("expense-tracker")

# Register all components
register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)

# Entry point for the MCP server
def main():
    """Main entry point for the MCP server"""
    mcp.run()

# Run the MCP server
if __name__ == "__main__":
    # For development
    main()