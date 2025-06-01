import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from app.main import app
from decimal import Decimal


@pytest.mark.asyncio
async def test_mcp_create_expense(mock_supabase_client, sample_category, sample_transaction, mock_supabase_response):
    """Test MCP expense creation endpoint"""
    # Mock category lookup (existing category)
    mock_supabase_client.table().select().eq().execute.return_value = mock_supabase_response([sample_category])
    # Mock transaction creation
    mock_supabase_client.table().insert().execute.return_value = mock_supabase_response([sample_transaction])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/mcp-tools/create-expense",
                json={
                    "date": "2024-01-30",
                    "amount": 25.50,
                    "merchant": "Test Store",
                    "category": "Test Category",
                    "notes": "MCP test transaction",
                    "tags": ["mcp", "test"]
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "transaction_id" in data
            assert data["merchant"] == "Test Store"
            assert data["category"] == "Test Category"


@pytest.mark.asyncio
async def test_mcp_get_categories(mock_supabase_client, sample_category, mock_supabase_response):
    """Test MCP categories endpoint"""
    mock_supabase_client.table().select().eq().range().execute.return_value = mock_supabase_response([sample_category])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/mcp-tools/categories")
            assert response.status_code == 200
            data = response.json()
            assert "categories" in data
            assert "total_categories" in data
            assert isinstance(data["categories"], list)


@pytest.mark.asyncio
async def test_mcp_spending_summary(mock_supabase_client, sample_transaction, mock_supabase_response):
    """Test MCP spending summary endpoint"""
    mock_supabase_client.table().select().order().range().execute.return_value = mock_supabase_response([sample_transaction])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/mcp-tools/spending-summary?days=30")
            assert response.status_code == 200
            data = response.json()
            assert "total_amount" in data
            assert "transaction_count" in data
            assert "top_categories" in data
            assert "date_range" in data


@pytest.mark.asyncio
async def test_mcp_auto_categorize(mock_supabase_client, sample_category, mock_supabase_response):
    """Test MCP auto-categorization endpoint"""
    mock_supabase_client.table().select().eq().range().execute.return_value = mock_supabase_response([sample_category])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/mcp-tools/auto-categorize",
                json={
                    "merchant": "Shell Gas Station",
                    "amount": 45.00
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "merchant" in data
            assert "suggested_category" in data
            assert "confidence" in data
            assert data["merchant"] == "Shell Gas Station"


@pytest.mark.asyncio
async def test_mcp_recent_transactions(mock_supabase_client, sample_transaction, sample_category, mock_supabase_response):
    """Test MCP recent transactions endpoint"""
    # Mock transaction fetch
    mock_supabase_client.table().select().order().range().execute.return_value = mock_supabase_response([sample_transaction])
    # Mock category fetch for each transaction
    mock_supabase_client.table().select().eq().execute.return_value = mock_supabase_response([sample_category])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/mcp-tools/recent-transactions?limit=5")
            assert response.status_code == 200
            data = response.json()
            assert "transactions" in data
            assert "count" in data
            assert isinstance(data["transactions"], list)


@pytest.mark.asyncio
async def test_mcp_create_expense_new_category(mock_supabase_client, sample_category, sample_transaction, mock_supabase_response):
    """Test MCP expense creation with new category"""
    # Mock category lookup (not found)
    mock_supabase_client.table().select().eq().execute.return_value = mock_supabase_response([])
    # Mock category creation
    mock_supabase_client.table().insert().execute.return_value = mock_supabase_response([sample_category])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/mcp-tools/create-expense",
                json={
                    "date": "2024-01-30",
                    "amount": 25.50,
                    "merchant": "New Store",
                    "category": "New Category",
                    "notes": "Test with new category"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["category"] == "New Category"


@pytest.mark.asyncio
async def test_mcp_create_expense_no_category(mock_supabase_client, sample_transaction, mock_supabase_response):
    """Test MCP expense creation without category"""
    mock_supabase_client.table().insert().execute.return_value = mock_supabase_response([sample_transaction])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/mcp-tools/create-expense",
                json={
                    "date": "2024-01-30",
                    "amount": 25.50,
                    "merchant": "Uncategorized Store",
                    "notes": "No category provided"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["category"] is None