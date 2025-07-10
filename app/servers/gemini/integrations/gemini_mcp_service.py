"""
Gemini AI service with persistent MCP integration
Uses application-level MCP connection management
"""
import os
import logging
from typing import Dict, Any, List, Optional
from google import genai
from app.servers.gemini.integrations.mcp_connection_manager import get_mcp_manager

logger = logging.getLogger(__name__)

# Suppress INFO logs from google_genai.models
# logging.getLogger('google_genai.models').setLevel(logging.WARNING)


class GeminiMCPService:
    """Gemini chat service using persistent MCP connections"""
    
    def __init__(self):
        """Initialize Gemini client"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"
        
        # Store conversation history
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        
        # Get the MCP connection manager
        self.mcp_manager = get_mcp_manager()
    
    async def send_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Send message to Gemini with MCP tools using persistent connection"""
        
        # Initialize conversation history if new session
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        try:
            response_text = ""
            function_calls = []
            
            # Use the persistent MCP session
            async with self.mcp_manager.get_session() as mcp_session:
                # Configure Gemini with MCP session
                config = genai.types.GenerateContentConfig(
                    temperature=0,
                    tools=[mcp_session],  # Use the persistent session
                )
                
                # Create chat with existing history
                chat = self.client.aio.chats.create(
                    model=self.model, 
                    config=config,
                    history=self._convert_history_to_gemini_format(
                        self.conversations[session_id]
                    )
                )
                
                # Send the message and get response
                response = await chat.send_message(message)
                response_text = response.text
                
                # Process function calls
                if hasattr(response, 'automatic_function_calling_history') and len(response.automatic_function_calling_history) > 0:
                    for call in response.automatic_function_calling_history:
                        if call.parts and len(call.parts) > 0:
                            part = call.parts[0]
                            
                            # Process function call
                            if hasattr(part, 'function_call') and part.function_call:
                                fc = part.function_call
                                function_calls.append({
                                    "type": "call",
                                    "name": fc.name,
                                    "args": dict(fc.args) if fc.args else {}
                                })
                                logger.info(f"Function call: {fc.name} with args: {fc.args}")
                            
                            # Process function response
                            elif hasattr(part, 'function_response') and part.function_response:
                                fr = part.function_response
                                result_text = ""
                                
                                # Extract result text if available
                                if isinstance(fr.response, dict) and 'result' in fr.response:
                                    result = fr.response['result']
                                    if hasattr(result, 'content') and result.content:
                                        if len(result.content) > 0 and hasattr(result.content[0], 'text'):
                                            result_text = result.content[0].text
                                
                                function_calls.append({
                                    "type": "response",
                                    "result": result_text or str(fr.response)
                                })
                                logger.info(f"Function response: {result_text or str(fr.response)}")
            
            # Update conversation history
            self.conversations[session_id].append({
                "role": "user",
                "content": message
            })
            self.conversations[session_id].append({
                "role": "assistant",
                "content": response_text,
                "function_calls": function_calls
            })
            
            return {
                "response": response_text,
                "function_calls": function_calls,
                "session_id": session_id
            }
                    
        except RuntimeError as e:
            if "MCP connection not initialized" in str(e):
                logger.error("MCP connection not initialized. Ensure app startup completed.")
                raise ValueError("Service not ready. Please try again in a moment.")
            else:
                logger.error(f"Runtime error in Gemini chat: {str(e)}", exc_info=True)
                raise
        except Exception as e:
            logger.error(f"Error in Gemini chat: {str(e)}", exc_info=True)
            # Return a user-friendly error message
            return {
                "response": f"I encountered an error while processing your request. Please try again.",
                "function_calls": [],
                "session_id": session_id
            }
    
    def _convert_history_to_gemini_format(self, history: List[Dict[str, Any]]) -> List:
        """Convert history to Gemini format"""
        gemini_history = []
        for msg in history:
            if msg["role"] in ["user", "assistant"]:
                gemini_history.append({
                    "role": "user" if msg["role"] == "user" else "model",
                    "parts": [{"text": msg["content"]}]
                })
        return gemini_history
    
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversations.get(session_id, [])
    
    async def close_session(self, session_id: str) -> None:
        """Close a session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
    
    async def close_all_sessions(self) -> None:
        """Close all sessions"""
        self.conversations.clear()