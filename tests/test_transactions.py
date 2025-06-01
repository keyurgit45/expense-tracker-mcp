import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_transaction(mock_supabase_client, sample_transaction, mock_supabase_response):
    """Test transaction creation with mocked database"""
    mock_supabase_client.table().insert().execute.return_value = mock_supabase_response([sample_transaction])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/transactions/",
                json={
                    "date": "2024-01-01",
                    "amount": 50.00,
                    "merchant": "Test Store",
                    "is_recurring": False
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["amount"] == "50.00"
            assert data["merchant"] == "Test Store"


@pytest.mark.asyncio
async def test_get_transactions(mock_supabase_client, sample_transaction, mock_supabase_response):
    """Test getting transactions with mocked database"""
    mock_supabase_client.table().select().order().range().execute.return_value = mock_supabase_response([sample_transaction])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v1/transactions/")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_transaction_by_id(mock_supabase_client, sample_transaction, mock_supabase_response):
    """Test getting single transaction by ID"""
    mock_supabase_client.table().select().eq().execute.return_value = mock_supabase_response([sample_transaction])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"/api/v1/transactions/{sample_transaction['transaction_id']}")
            assert response.status_code == 200
            data = response.json()
            assert data["transaction_id"] == sample_transaction["transaction_id"]


@pytest.mark.asyncio
async def test_update_transaction(mock_supabase_client, sample_transaction, mock_supabase_response):
    """Test updating a transaction"""
    updated_transaction = sample_transaction.copy()
    updated_transaction["amount"] = "75.00"
    
    mock_supabase_client.table().update().eq().execute.return_value = mock_supabase_response([updated_transaction])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.put(
                f"/api/v1/transactions/{sample_transaction['transaction_id']}",
                json={"amount": 75.00}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["amount"] == "75.00"


@pytest.mark.asyncio
async def test_delete_transaction(mock_supabase_client, sample_transaction, mock_supabase_response):
    """Test deleting a transaction"""
    mock_supabase_client.table().delete().eq().execute.return_value = mock_supabase_response([sample_transaction])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.delete(f"/api/v1/transactions/{sample_transaction['transaction_id']}")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data