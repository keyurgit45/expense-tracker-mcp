# Gemini Server API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Most endpoints require JWT Bearer token authentication. Include the token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## Endpoints

### 1. Health Check
Check if the server is running and healthy.

**Endpoint:** `GET /health`  
**Authentication:** Not required  
**Request:** None  
**Response:**
```json
{
  "status": "healthy",
  "service": "gemini-chat"
}
```
**Status Codes:**
- `200 OK` - Server is healthy

**Example:**
```bash
curl http://localhost:8000/health
```

---

### 2. Root Information
Get information about available endpoints.

**Endpoint:** `GET /`  
**Authentication:** Not required  
**Request:** None  
**Response:**
```json
{
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
```
**Status Codes:**
- `200 OK` - Success

**Example:**
```bash
curl http://localhost:8000/
```

---

### 3. User Signup
Register a new user account.

**Endpoint:** `POST /api/v1/auth/signup`  
**Authentication:** Not required  
**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```
**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsImtpZCI6...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "oyi5k3sjvs3r"
}
```
**Status Codes:**
- `200 OK` - Account created successfully
- `400 Bad Request` - User registration failed (invalid data or email already exists)
- `422 Unprocessable Entity` - Invalid request format

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com", "password": "TestPassword123"}'
```

---

### 4. User Login
Authenticate existing user.

**Endpoint:** `POST /api/v1/auth/login`  
**Authentication:** Not required  
**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```
**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsImtpZCI6...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "4pimdcx4n5tw"
}
```
**Status Codes:**
- `200 OK` - Login successful
- `401 Unauthorized` - Invalid credentials

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com", "password": "TestPassword123"}'
```

---

### 5. Refresh Token
Get a new access token using refresh token.

**Endpoint:** `POST /api/v1/auth/refresh`  
**Authentication:** Not required  
**Request Body:**
```json
{
  "refresh_token": "4pimdcx4n5tw"
}
```
**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsImtpZCI6...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "ubkttvr4uh2t"
}
```
**Status Codes:**
- `200 OK` - Token refreshed successfully
- `401 Unauthorized` - Invalid refresh token

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "4pimdcx4n5tw"}'
```

---

### 6. Get Current User
Get information about the authenticated user.

**Endpoint:** `GET /api/v1/auth/me`  
**Authentication:** Required  
**Request:** None (requires Bearer token in header)  
**Response:**
```json
{
  "id": "3a791e97-53a3-42e4-9af1-16ccd2c8a440",
  "email": "user@example.com",
  "role": "authenticated",
  "aud": "authenticated",
  "exp": 1752264899,
  "iat": 1752261299,
  "iss": "https://lfhtrktbormrlpnoih.supabase.co/auth/v1",
  "sub": "3a791e97-53a3-42e4-9af1-16ccd2c8a440"
}
```
**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Invalid or missing token

**Example:**
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsImtpZCI6..."
```

---

### 7. Logout
Sign out the current user.

**Endpoint:** `POST /api/v1/auth/logout`  
**Authentication:** Required  
**Request:** None (requires Bearer token in header)  
**Response:**
```json
{
  "message": "Logged out successfully"
}
```
**Status Codes:**
- `200 OK` - Logout successful
- `401 Unauthorized` - Invalid or missing token

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsImtpZCI6..."
```

---

### 8. Chat
Send a message to the AI assistant for expense tracking.

**Endpoint:** `POST /api/v1/chat`  
**Authentication:** Required  
**Request Body:**
```json
{
  "message": "What is my spending for last month?",
  "session_id": "unique-session-id"
}
```
**Response:**
```json
{
  "response": "Based on your transaction history, your total spending last month was $2,450. The main categories were: Groceries ($650), Rent ($1,200), Transportation ($350), and Entertainment ($250).",
  "session_id": "unique-session-id"
}
```
**Status Codes:**
- `200 OK` - Chat response generated
- `401 Unauthorized` - Invalid or missing token
- `422 Unprocessable Entity` - Invalid request format

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsImtpZCI6..." \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my spending for last month?", "session_id": "session-123"}'
```

---

### 9. Chat History
Get conversation history for a specific session.

**Endpoint:** `GET /api/v1/chat/history/{session_id}`  
**Authentication:** Required  
**Request:** None (session_id in URL path)  
**Response:**
```json
{
  "session_id": "unique-session-id",
  "messages": [
    {
      "role": "user",
      "content": "What is my spending for last month?",
      "timestamp": "2024-01-10T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Based on your transaction history, your total spending last month was $2,450...",
      "timestamp": "2024-01-10T10:30:05Z"
    }
  ]
}
```
**Status Codes:**
- `200 OK` - History retrieved
- `401 Unauthorized` - Invalid or missing token
- `404 Not Found` - Session not found

**Example:**
```bash
curl -X GET http://localhost:8000/api/v1/chat/history/session-123 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsImtpZCI6..."
```

---

## Error Response Format
All error responses follow this format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Notes
- Access tokens expire after 1 hour (3600 seconds)
- Use the refresh token endpoint to get a new access token
- All timestamps are in ISO 8601 format
- The chat endpoint integrates with MCP tools for expense tracking functionality