import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_tag(mock_supabase_client, sample_tag, mock_supabase_response):
    """Test tag creation with mocked database"""
    # Mock check for existing tag (should return empty)
    mock_supabase_client.table().select().eq().execute.return_value = mock_supabase_response([])
    # Mock successful creation
    mock_supabase_client.table().insert().execute.return_value = mock_supabase_response([sample_tag])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/tags/",
                json={"value": "test_tag"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["value"] == "test_tag"


@pytest.mark.asyncio
async def test_get_tags(mock_supabase_client, sample_tag, mock_supabase_response):
    """Test getting tags with mocked database"""
    mock_supabase_client.table().select().range().execute.return_value = mock_supabase_response([sample_tag])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v1/tags/")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_tag_by_id(mock_supabase_client, sample_tag, mock_supabase_response):
    """Test getting single tag by ID"""
    mock_supabase_client.table().select().eq().execute.return_value = mock_supabase_response([sample_tag])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"/api/v1/tags/{sample_tag['tag_id']}")
            assert response.status_code == 200
            data = response.json()
            assert data["tag_id"] == sample_tag["tag_id"]
            assert data["value"] == sample_tag["value"]


@pytest.mark.asyncio
async def test_delete_tag(mock_supabase_client, sample_tag, mock_supabase_response):
    """Test deleting a tag"""
    # Mock deleting transaction_tags relationships first
    mock_supabase_client.table().delete().eq().execute.return_value = mock_supabase_response([])
    # Mock deleting the tag itself
    mock_supabase_client.table().delete().eq().execute.return_value = mock_supabase_response([sample_tag])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.delete(f"/api/v1/tags/{sample_tag['tag_id']}")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data


@pytest.mark.asyncio
async def test_add_tag_to_transaction(mock_supabase_client, sample_tag, sample_transaction, mock_supabase_response):
    """Test adding a tag to a transaction"""
    transaction_tag = {
        "transaction_id": sample_transaction["transaction_id"],
        "tag_id": sample_tag["tag_id"]
    }
    
    mock_supabase_client.table().insert().execute.return_value = mock_supabase_response([transaction_tag])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/tags/transaction-tags/",
                json={
                    "transaction_id": sample_transaction["transaction_id"],
                    "tag_id": sample_tag["tag_id"]
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "message" in data