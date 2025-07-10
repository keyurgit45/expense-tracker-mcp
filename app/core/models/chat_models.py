"""
Models for chat functionality
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    function_calls: Optional[List[Dict[str, Any]]] = Field(
        default=None, 
        description="Function calls made by the assistant"
    )


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., min_length=1, description="User message to send to Gemini")
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation continuity. If not provided, a new session will be created"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(..., description="Gemini's response")
    session_id: str = Field(..., description="Session ID for future messages")
    function_calls: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of function calls made during the response"
    )


class ChatHistoryResponse(BaseModel):
    """Response model for chat history"""
    session_id: str
    history: List[ChatMessage]
    message_count: int