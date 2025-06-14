# Expense Tracker MCP Server

A production-ready FastAPI MCP (Model Context Protocol) server for automated expense management with Supabase backend and hierarchical category support.

## 🚀 Features

- **FastAPI MCP Server**: RESTful API with automatic OpenAPI documentation
- **Hierarchical Categories**: Parent-child category relationships for better organization
- **Supabase Integration**: PostgreSQL database with real-time capabilities
- **Complete CRUD Operations**: Categories, Transactions, Tags with many-to-many relationships
- **AI-Powered Categorization**: Automatic transaction categorization using embeddings and similarity search
- **Learning System**: Improves categorization accuracy over time based on user feedback
- **Predefined Tags**: Enforced tag system for consistency (subscriptions, payment methods, etc.)
- **Safe Testing**: Comprehensive mocked tests that don't hit production database
- **Production Ready**: Error handling, validation, safety checks, and documentation

## 📊 Database Schema

### Tables
- **Categories**: Expense/income categories with hierarchical support
- **Transactions**: Individual expense/income records
- **Tags**: Flexible tagging system with predefined values
- **Transaction_Tags**: Many-to-many junction table
- **Transaction_Embeddings**: Vector embeddings for AI categorization

### Hierarchical Categories
```
💸 Food & Dining
   ├── Groceries
   ├── Restaurants & Takeout
   └── Coffee & Beverages

💸 Housing & Utilities
   ├── Rent/Mortgage
   ├── Electricity
   ├── Water
   └── Internet
   
💰 Primary Income
   ├── Salary
   └── Bonuses
```

## 🛠️ Quick Start

### 1. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
cp .env.example .env
# Add your Supabase credentials to .env
```

### 3. Create Database Tables
Execute this SQL in your Supabase SQL Editor:

```sql
-- Categories table
CREATE TABLE categories (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    parent_category_id UUID REFERENCES categories(category_id)
);

-- Transactions table
CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    merchant TEXT,
    category_id UUID REFERENCES categories(category_id),
    is_recurring BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tags table
CREATE TABLE tags (
    tag_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    value TEXT NOT NULL UNIQUE
);

-- Transaction_Tags junction table
CREATE TABLE transaction_tags (
    transaction_id UUID NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(tag_id) ON DELETE CASCADE,
    PRIMARY KEY (transaction_id, tag_id)
);

-- Update trigger for transactions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE
    ON transactions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 4. Run the Server
```bash
python scripts/run_server.py
```

### 5. Populate Categories
```bash
python scripts/populate_hierarchical_categories.py
```

### 6. View Categories
```bash
python scripts/show_categories.py
```

### 7. Test MCP Integration
```bash
python scripts/mcp_demo.py
```

## 📡 API Endpoints

### Categories
- `POST /api/v1/categories/` - Create category
- `GET /api/v1/categories/` - List categories
- `GET /api/v1/categories/{id}` - Get category
- `PUT /api/v1/categories/{id}` - Update category
- `DELETE /api/v1/categories/{id}` - Soft delete category

### Transactions
- `POST /api/v1/transactions/` - Create transaction
- `GET /api/v1/transactions/` - List transactions
- `GET /api/v1/transactions/{id}` - Get transaction
- `GET /api/v1/transactions/{id}/with-tags` - Get transaction with tags
- `PUT /api/v1/transactions/{id}` - Update transaction
- `DELETE /api/v1/transactions/{id}` - Delete transaction

### Tags
- `POST /api/v1/tags/` - Create tag
- `GET /api/v1/tags/` - List tags
- `GET /api/v1/tags/{id}` - Get tag
- `DELETE /api/v1/tags/{id}` - Delete tag
- `POST /api/v1/tags/transaction-tags/` - Add tag to transaction
- `DELETE /api/v1/tags/transaction-tags/{transaction_id}/{tag_id}` - Remove tag from transaction

## 🧪 Testing

**✅ Safe Testing with Mocks**

Tests use mocked database responses instead of hitting real Supabase:

```bash
# Run all tests with mocks (safe)
ENVIRONMENT=test pytest tests/ -v

# Run specific test file
ENVIRONMENT=test pytest tests/test_categories.py -v

# Test MCP tools specifically
ENVIRONMENT=test pytest tests/test_mcp_tools.py -v
```

**🛡️ Database Safety**
- Tests use mock fixtures instead of real database calls
- Scripts include environment safety checks
- Production database protection enabled

## 🚀 Continuous Integration

This project uses GitHub Actions for automated testing and quality assurance:

### Workflows
- **Tests**: Run on Python 3.10, 3.11, 3.12 with mocked database
- **Lint**: Code formatting (black), import sorting (isort), linting (flake8)
- **Security**: Dependency scanning (safety), security linting (bandit), secret detection
- **Coverage**: Test coverage reporting with Codecov integration

### Status Badges
Add these to your GitHub repo for status visibility:
```markdown
![Tests](https://github.com/YOUR_USERNAME/expense-tracker-mcp-server/workflows/Tests/badge.svg)
![Lint](https://github.com/YOUR_USERNAME/expense-tracker-mcp-server/workflows/Lint/badge.svg)
![Security](https://github.com/YOUR_USERNAME/expense-tracker-mcp-server/workflows/Security/badge.svg)
![Coverage](https://github.com/YOUR_USERNAME/expense-tracker-mcp-server/workflows/Coverage/badge.svg)
```

## 🌍 Environment Variables

```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
ENVIRONMENT=development  # development, test, production
```

## 🏗️ Development

The server runs with auto-reload enabled for development. API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Project Structure

```
ExpenseTracker/
├── app/
│   ├── api/v1/           # API endpoints
│   ├── crud/             # Database operations
│   ├── models/           # Pydantic models
│   ├── schemas/          # Request/response schemas
│   ├── mcp/             # MCP server components
│   │   ├── tools.py     # MCP tool implementations
│   │   ├── resources.py # MCP resources
│   │   ├── prompts.py   # System prompts
│   │   └── tags_config.py # Predefined tags
│   ├── services/        # Business logic services
│   │   ├── embeddings.py # OpenAI embeddings service
│   │   └── categorization.py # AI categorization logic
│   ├── config.py         # Settings management
│   ├── database.py       # Supabase client
│   └── main.py          # FastAPI app
├── tests/               # Pytest test suite with mocks
├── scripts/             # Utility scripts
├── docs/               # Documentation
└── pyproject.toml      # Project configuration
```

## 🤖 MCP Integration

This server implements the **Model Context Protocol (MCP)** using `fastapi-mcp` for seamless LLM integration. It provides both REST API endpoints and MCP tools for AI agents.

### MCP Tools Available

#### 🔧 **create-expense**
Create expenses from LLM-parsed bank statements:
```bash
curl -X POST "http://localhost:8000/mcp-tools/create-expense" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-01-30",
    "amount": 25.50,
    "merchant": "Starbucks Coffee",
    "category": "Coffee & Beverages",
    "notes": "Morning coffee",
    "tags": ["business", "coffee"]
  }'
```

#### 📊 **spending-summary**
Get spending analytics for LLM insights:
```bash
curl "http://localhost:8000/mcp-tools/spending-summary?days=30"
```

#### 📁 **categories**
Get all categories for LLM categorization:
```bash
curl "http://localhost:8000/mcp-tools/categories"
```

#### 🤖 **auto-categorize**
Auto-suggest categories based on merchant:
```bash
curl -X POST "http://localhost:8000/mcp-tools/auto-categorize" \
  -H "Content-Type: application/json" \
  -d '{"merchant": "Shell Gas Station", "amount": 45.00}'
```

#### 📝 **recent-transactions**
Get recent transactions for context:
```bash
curl "http://localhost:8000/mcp-tools/recent-transactions?limit=10"
```

### Using with LLM Agents

The FastAPI-MCP integration automatically exposes these tools via the MCP protocol at `/mcp`. LLM agents can:

1. **Parse PDF bank statements** and call `create-expense` for each transaction
2. **Auto-categorize** expenses using `auto-categorize` 
3. **Provide insights** using `spending-summary` and `recent-transactions`
4. **Smart categorization** by understanding the category hierarchy

### Example LLM Workflow

```
1. User uploads bank statement PDF
2. LLM parses transactions from PDF
3. For each transaction:
   - LLM calls auto-categorize to suggest category
   - LLM calls create-expense to store transaction
4. LLM calls spending-summary to provide insights
```
{
    "mcpServers": {
      "expense-tracker": {
         "command": "/opt/homebrew/bin/uv",
       "args": [
          "run",
          "--directory",
          "/Users/keyur/Code/Projects/ExpenseTracker",
          "python",
          "run_mcp.py"
        ],
        "cwd": "/Users/keyur/Code/Projects/ExpenseTracker",
        "env": {
          "SUPABASE_URL": "",
          "SUPABASE_KEY": "",
          "ENVIRONMENT": "development"
        }
      }
    }
}

## 🧠 AI-Powered Categorization

The expense tracker uses a hybrid approach for intelligent transaction categorization:

### How It Works

1. **Embedding Generation**: Each transaction is converted to text format and embedded using Sentence Transformers (free, local)
2. **Similarity Search**: Uses pgvector to find similar past transactions
3. **Smart Voting**: Uses weighted voting from similar transactions to predict category
4. **Rule-Based Fallback**: Comprehensive rules for common merchant patterns
5. **Continuous Learning**: User confirmations improve future predictions

### Setup AI Categorization

1. **Enable pgvector** (already done in your Supabase instance)

2. **Create embeddings table**:
   ```bash
   # Run the SQL script in Supabase SQL Editor
   scripts/create_embeddings_schema.sql
   ```

3. **Populate predefined tags**:
   ```bash
   python scripts/populate_predefined_tags.py
   ```

4. **Install dependencies** - Sentence Transformers will download the model on first use (~90MB)

### MCP Tools for AI Features

- **auto_categorize_transaction**: Automatically categorize uncategorized transactions
- **confirm_transaction_category**: Confirm/correct categories to improve learning
- **analyze_subscriptions**: Identify and analyze recurring payments

### Predefined Tags System

The system enforces consistent tagging with 17 predefined tags:
- **Subscription Types**: annual-subscription, monthly-subscription, quarterly-subscription
- **Expense Types**: recurring, one-time, subscription
- **Categories**: business, personal, travel, online
- **Special**: tax-deductible, reimbursable, shared
- **Payment Methods**: cash, credit-card, debit-card, bank-transfer

### Example Usage

```python
# Auto-categorize a transaction
result = await auto_categorize_transaction(
    transaction_id="uuid-here",
    use_embeddings=True
)

# Confirm category for learning
await confirm_transaction_category(
    transaction_id="uuid-here", 
    category_name="Food & Dining",
    store_embedding=True
)
```