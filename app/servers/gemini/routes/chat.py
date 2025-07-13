"""
Chat endpoint for Gemini AI integration with JWT authentication
"""
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from app.core.models.chat_models import ChatRequest, ChatResponse, ChatHistoryResponse, ChatMessage
from app.core.models.auth_models import UserInfo
from app.servers.gemini.integrations.gemini_mcp_service import GeminiMCPService as GeminiChatService
from app.servers.gemini.auth.jwt_auth import get_current_user, get_optional_user

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
    current_user: UserInfo = Depends(get_current_user),
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
    
    Requires authentication.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Add user context to the message
        user_message = f"[User: {current_user.email}] {request.message}"
        
        # Send message to Gemini
        result = await gemini_service.send_message(session_id, user_message)
        
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
    current_user: UserInfo = Depends(get_current_user),
    gemini_service: GeminiChatService = Depends(get_gemini_service)
):
    """
    Get the conversation history for a specific session.
    
    Requires authentication.
    """
    raw_history = await gemini_service.get_session_history(session_id)

    # Convert raw dicts to ChatMessage objects for type safety
    parsed_history = [ChatMessage(**msg) for msg in raw_history]

    return ChatHistoryResponse(
        session_id=session_id,
        history=parsed_history,
        message_count=len(parsed_history)
    )


@router.delete("/chat/session/{session_id}")
async def close_chat_session(
    session_id: str,
    current_user: UserInfo = Depends(get_current_user),
    gemini_service: GeminiChatService = Depends(get_gemini_service)
):
    """
    Close a chat session and free up resources.
    
    Requires authentication.
    """
    await gemini_service.close_session(session_id)
    return {"message": f"Session {session_id} closed successfully"}


async def cleanup_sessions():
    """Cleanup all sessions on shutdown"""
    if _gemini_service:
        await _gemini_service.close_all_sessions()