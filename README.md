# Expense Tracker Backend

AI-powered expense tracking system with natural language interface, intelligent categorization, and real-time sync.

## Architecture

The system uses a two-server architecture:

1. **MCP Server**: Core expense tracking tools exposed via Model Context Protocol
2. **Gemini AI Server**: FastAPI server providing chat interface with authentication

## Features

- 🤖 Natural language expense management via Gemini AI
- 🧠 Intelligent categorization using embeddings and similarity search
- 🔐 JWT authentication with Supabase
- 📊 Hierarchical categories for organization
- 🏷️ Predefined tag system
- 📈 Real-time data sync
- 🔄 Learning system that improves over time

## Quick Start

### Prerequisites
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Setup
```bash
cp .env.example .env
# Add your credentials:
# - SUPABASE_URL
# - SUPABASE_KEY
# - GOOGLE_API_KEY (for Gemini)
```

### Database Setup
Execute the SQL scripts in your Supabase SQL Editor:
```bash
# Core tables
scripts/create_tables.sql
# Embeddings support
scripts/create_embeddings_schema.sql
```

### Run Both Servers

Terminal 1 - MCP Server:
```bash
python run_mcp.py
```

Terminal 2 - Gemini AI Server:
```bash
uvicorn app.servers.gemini.main:app --reload --port 8000
```

### Initialize Data
```bash
# Populate categories
python scripts/populate_hierarchical_categories.py

# Populate predefined tags
python scripts/populate_predefined_tags.py
```

## API Endpoints

### Chat Interface
- `POST /chat` - Send natural language commands
- `POST /auth/refresh` - Refresh JWT token

### MCP Tools (via chat)
- Create expenses from natural language
- Auto-categorize transactions
- Get spending summaries
- Analyze subscriptions
- View recent transactions

## Flutter Client

refer https://github.com/keyurgit45/expense-tracker-client

## Testing
```bash
# Run all tests with mocks
ENVIRONMENT=test pytest tests/ -v

# Run specific components
ENVIRONMENT=test pytest tests/test_mcp_tools.py -v
ENVIRONMENT=test pytest tests/test_categorization.py -v
```

## Project Structure
```
backend/
├── app/
│   ├── core/              # Business logic
│   ├── servers/
│   │   ├── gemini/       # AI chat server
│   │   └── mcp/          # MCP tool server
│   └── shared/           # Shared configs
├── scripts/              # Utilities
└── tests/               # Test suite
```

## AI Categorization

The system uses a hybrid approach:
1. Generates embeddings for transactions using Sentence Transformers
2. Finds similar past transactions using pgvector
3. Uses weighted voting to predict categories
4. Falls back to rule-based matching
5. Learns from user confirmations

## Development

- API docs: http://localhost:8000/docs
- Frontend integration: Configure CORS in Gemini server
- MCP tools can be tested directly via chat interface
