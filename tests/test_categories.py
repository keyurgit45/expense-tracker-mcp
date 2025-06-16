import pytest
from unittest.mock import patch, Mock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.schemas.schemas import CategoryResponse


@pytest.mark.asyncio
async def test_create_category(mock_supabase_client, sample_category, mock_supabase_response):
    """Test category creation with mocked database"""
    # Setup mock response
    mock_supabase_client.table().insert().execute.return_value = mock_supabase_response([sample_category])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/categories/",
                json={"name": "Test Category", "is_active": True}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Category"
            assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_categories(mock_supabase_client, sample_category, mock_supabase_response):
    """Test getting categories with mocked database"""
    # Setup mock response
    mock_supabase_client.table().select().eq().range().execute.return_value = mock_supabase_response([sample_category])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v1/categories/")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            if data:  # If we have data, verify structure
                assert "category_id" in data[0]
                assert "name" in data[0]


@pytest.mark.asyncio
async def test_get_category_by_id(mock_supabase_client, sample_category, mock_supabase_response):
    """Test getting single category by ID"""
    # Setup the mock response for this specific test
    mock_supabase_client.table().execute.return_value = mock_supabase_response([sample_category])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"/api/v1/categories/{sample_category['category_id']}")
            assert response.status_code == 200
            data = response.json()
            assert data["category_id"] == sample_category["category_id"]
            assert data["name"] == sample_category["name"]


@pytest.mark.asyncio
async def test_update_category(mock_supabase_client, sample_category, mock_supabase_response):
    """Test updating a category"""
    updated_category = sample_category.copy()
    updated_category["name"] = "Updated Category"
    
    mock_supabase_client.table().execute.return_value = mock_supabase_response([updated_category])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.put(
                f"/api/v1/categories/{sample_category['category_id']}",
                json={"name": "Updated Category"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Category"


@pytest.mark.asyncio
async def test_delete_category(mock_supabase_client, sample_category, mock_supabase_response):
    """Test soft deleting a category"""
    deleted_category = sample_category.copy()
    deleted_category["is_active"] = False
    
    mock_supabase_client.table().execute.return_value = mock_supabase_response([deleted_category])
    
    with patch('app.database.supabase', mock_supabase_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.delete(f"/api/v1/categories/{sample_category['category_id']}")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data