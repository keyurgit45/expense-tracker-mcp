from fastapi import FastAPI
from app.api.v1 import categories, transactions, tags

app = FastAPI(
    title="Expense Tracker",
    description="A FastAPI expense tracking application with Supabase backend and MCP integration",
    version="1.0.0"
)

# Include REST API routes
app.include_router(categories.router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])
app.include_router(tags.router, prefix="/api/v1/tags", tags=["tags"])


@app.get("/")
async def root():
    return {
        "message": "Expense Tracker is running",
        "features": [
            "REST API for expense management",
            "MCP server for LLM integration",
            "Supabase backend storage"
        ],
        "endpoints": {
            "api": "/api/v1/",
            "docs": "/docs",
            "mcp_server": "Run with: python scripts/run_mcp_server.py"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/mcp-info")
async def mcp_info():
    """Information about MCP integration"""
    return {
        "mcp_available": True,
        "server_script": "scripts/run_mcp_server.py",
        "tools": [
            "create_expense",
            "get_spending_summary", 
            "get_available_categories",
            "auto_categorize_merchant",
            "get_recent_transactions"
        ],
        "resources": [
            "expense-tracker://categories",
            "expense-tracker://recent-transactions"
        ],
        "claude_desktop_config": {
            "mcpServers": {
                "expense-tracker": {
                    "command": "python",
                    "args": [f"{app.extra['project_root']}/scripts/run_mcp_server.py"],
                    "env": {}
                }
            }
        }
    }


# Store project root for MCP config
import os
app.extra = {"project_root": os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}