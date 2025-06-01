from fastapi import FastAPI
from app.api.v1 import categories, transactions, tags

app = FastAPI(
    title="Expense Tracker MCP Server",
    description="A FastAPI MCP server for expense tracking with Supabase backend",
    version="1.0.0"
)

app.include_router(categories.router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])
app.include_router(tags.router, prefix="/api/v1/tags", tags=["tags"])


@app.get("/")
async def root():
    return {"message": "Expense Tracker MCP Server is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}