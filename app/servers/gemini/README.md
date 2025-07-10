# Gemini AI Chat Server

This server provides a chat interface powered by Google's Gemini AI with access to expense tracking tools via MCP (Model Context Protocol).

## Features

- **Natural Language Interface**: Chat with Gemini to manage expenses
- **MCP Integration**: Gemini can use expense tracking tools
- **Session Management**: Maintain conversation context
- **Function Transparency**: See what tools Gemini uses

## Setup

1. **Set your Gemini API Key**:
   ```bash
   export GEMINI_API_KEY=your_api_key_here
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Run the server**:
   ```bash
   uv run uvicorn app.servers.gemini.main:app --reload
   ```

## API Endpoints

### Health Check
```
GET /health
```

### Chat with Gemini
```
POST /api/v1/chat
Content-Type: application/json

{
  "message": "I spent $50 on groceries today",
  "session_id": "optional-session-id"
}
```

Response:
```json
{
  "response": "I've recorded your grocery expense of $50...",
  "session_id": "generated-or-provided-session-id",
  "function_calls": [
    {
      "type": "call",
      "name": "create_expense",
      "args": {"amount": -50, "merchant": "Grocery Store", ...}
    }
  ]
}
```

### Get Chat History
```
GET /api/v1/chat/history/{session_id}
```

### Close Session
```
DELETE /api/v1/chat/session/{session_id}
```

## Example Usage

```python
import httpx

# Chat with Gemini
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/chat",
        json={"message": "Show me my spending this month"}
    )
    print(response.json())
```

## What Gemini Can Do

- Create and categorize expenses
- Analyze spending patterns
- Provide financial insights
- Answer questions about your transactions
- Generate spending summaries

## Architecture

The server uses:
- **FastAPI** for the REST API
- **Google Gemini** for AI capabilities
- **MCP** for tool integration
- **Async/await** for performance