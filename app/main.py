from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from app.api.v1 import categories, transactions, tags
from app.mcp_tools import mcp_router

app = FastAPI(
    title="Expense Tracker MCP Server",
    description="A FastAPI MCP server for expense tracking with Supabase backend and LLM integration",
    version="1.0.0"
)

# Include regular REST API routes
app.include_router(categories.router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])
app.include_router(tags.router, prefix="/api/v1/tags", tags=["tags"])

# Include MCP tools (these will be automatically exposed via MCP protocol)
app.include_router(mcp_router)

# Initialize MCP integration
mcp = FastApiMCP(app)


@app.get("/")
async def root():
    return {"message": "Expense Tracker MCP Server is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Mount MCP server
mcp.mount()