# Gemini AI Chat Server with JWT Authentication

This server provides a chat interface powered by Google's Gemini AI with access to expense tracking tools via MCP (Model Context Protocol) and JWT authentication using Supabase.

## Features

- **JWT Authentication**: Secure user authentication with Supabase
- **Natural Language Interface**: Chat with Gemini to manage expenses
- **MCP Integration**: Gemini can use expense tracking tools
- **Session Management**: Maintain conversation context
- **Function Transparency**: See what tools Gemini uses
- **User Context**: Personalized responses based on authenticated user

## Setup

1. **Set your environment variables**:
   ```bash
   export GEMINI_API_KEY=your_gemini_api_key_here
   export SUPABASE_URL=your_supabase_project_url
   export SUPABASE_KEY=your_supabase_anon_key
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Run the server**:
   ```bash
   uv run uvicorn app.servers.gemini.main:app --reload
   ```

## Authentication

### User Registration
```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### User Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "refresh_token_here"
}
```

### Refresh Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your_refresh_token_here"
  }'
```

### Get Current User
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer your_access_token_here"
```

## API Endpoints

### Health Check
```
GET /health
```

### Chat with Gemini (Requires Authentication)
```
POST /api/v1/chat
Authorization: Bearer your_access_token_here
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

### Get Chat History (Requires Authentication)
```
GET /api/v1/chat/history/{session_id}
Authorization: Bearer your_access_token_here
```

### Close Session (Requires Authentication)
```
DELETE /api/v1/chat/session/{session_id}
Authorization: Bearer your_access_token_here
```

## Example Usage with Authentication

```python
import httpx

# Login to get access token
async with httpx.AsyncClient() as client:
    login_response = await client.post(
        "http://localhost:8000/api/v1/auth/login",
        json={
            "email": "user@example.com",
            "password": "securepassword123"
        }
    )
    
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    # Chat with Gemini using the access token
    chat_response = await client.post(
        "http://localhost:8000/api/v1/chat",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"message": "Show me my spending this month"}
    )
    
    print(chat_response.json())
```

## What Gemini Can Do

- Create and categorize expenses
- Analyze spending patterns
- Provide financial insights
- Answer questions about your transactions
- Generate spending summaries
- Provide personalized responses based on user context

## Architecture

The server uses:
- **FastAPI** for the REST API
- **Supabase** for JWT authentication and user management
- **Google Gemini** for AI capabilities
- **MCP** for tool integration
- **Async/await** for performance
- **CORS** for frontend integration

## Security Features

- **JWT Token Authentication**: Secure user sessions
- **Token Refresh**: Automatic token renewal
- **User Context**: Personalized responses
- **CORS Protection**: Configurable cross-origin requests
- **Input Validation**: Pydantic models for request validation

## Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Optional
ENVIRONMENT=development  # development, test, production
```

## Frontend Integration

For frontend applications, include the access token in the Authorization header:

```javascript
const response = await fetch('/api/v1/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  },
  body: JSON.stringify({
    message: 'I spent $50 on groceries today'
  })
});
```