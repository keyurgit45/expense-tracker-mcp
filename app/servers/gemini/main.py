from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.servers.gemini.routes import chat, auth
from app.servers.gemini.integrations.mcp_connection_manager import get_mcp_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MCP connection
    logger.info("Starting up Gemini server...")
    mcp_manager = get_mcp_manager()
    
    try:
        await mcp_manager.initialize()
        logger.info("MCP connection initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MCP connection: {str(e)}")
        # Continue without MCP if initialization fails
        # The service will handle this gracefully
    
    yield
    
    # Shutdown: Clean up MCP connection
    logger.info("Shutting down Gemini server...")
    await mcp_manager.shutdown()
    await chat.cleanup_sessions()


app = FastAPI(
    title="Expense Tracker Gemini AI Chat",
    description="Gemini AI chat interface for expense tracking with MCP tools integration and JWT authentication",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])


@app.get("/")
async def root():
    return {
        "service": "Gemini AI Chat for Expense Tracking",
        "authentication": {
            "login": "POST /api/v1/auth/login",
            "signup": "POST /api/v1/auth/signup",
            "refresh": "POST /api/v1/auth/refresh",
            "logout": "POST /api/v1/auth/logout",
            "me": "GET /api/v1/auth/me"
        },
        "endpoints": {
            "chat": "POST /api/v1/chat",
            "history": "GET /api/v1/chat/history/{session_id}",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "gemini-chat"}