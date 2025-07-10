"""
Chat endpoint for Gemini AI integration
"""
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from app.core.models.chat_models import ChatRequest, ChatResponse, ChatHistoryResponse
from app.servers.gemini.integrations.gemini_mcp_service import GeminiMCPService as GeminiChatService

router = APIRouter()

# Singleton Gemini service
_gemini_service: Optional[GeminiChatService] = None


async def get_gemini_service() -> GeminiChatService:
    """Get or create Gemini service instance"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiChatService()
    return _gemini_service


@router.post("/chat", response_model=ChatResponse)
async def chat_with_gemini(
    request: ChatRequest,
    gemini_service: GeminiChatService = Depends(get_gemini_service)
):
    """
    Send a message to Gemini AI with access to expense tracking tools.
    
    The AI can help with:
    - Creating and managing expenses
    - Analyzing spending patterns
    - Categorizing transactions
    - Answering questions about your finances
    
    If no session_id is provided, a new conversation session will be created.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Send message to Gemini
        result = await gemini_service.send_message(session_id, request.message)
        
        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
            function_calls=result["function_calls"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.get("/chat/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    gemini_service: GeminiChatService = Depends(get_gemini_service)
):
    """
    Get the conversation history for a specific session.
    """
    history = await gemini_service.get_session_history(session_id)
    
    return ChatHistoryResponse(
        session_id=session_id,
        history=history,
        message_count=len(history)
    )


@router.delete("/chat/session/{session_id}")
async def close_chat_session(
    session_id: str,
    gemini_service: GeminiChatService = Depends(get_gemini_service)
):
    """
    Close a chat session and free up resources.
    """
    await gemini_service.close_session(session_id)
    return {"message": f"Session {session_id} closed successfully"}


async def cleanup_sessions():
    """Cleanup all sessions on shutdown"""
    if _gemini_service:
        await _gemini_service.close_all_sessions()