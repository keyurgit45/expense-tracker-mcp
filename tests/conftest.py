import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone
import os

# Set test environment
os.environ["ENVIRONMENT"] = "test"


@pytest.fixture
def mock_supabase_response():
    """Mock Supabase response structure"""
    def create_response(data=None, count=None):
        response = Mock()
        response.data = data or []
        response.count = count
        return response
    return create_response


@pytest.fixture
def mock_supabase_client(mock_supabase_response):
    """Mock Supabase client for testing"""
    client = Mock()
    
    # Create a shared table mock that can be configured per test
    table_mock = Mock()
    
    # All methods return the same mock to allow chaining
    table_mock.insert.return_value = table_mock
    table_mock.select.return_value = table_mock
    table_mock.update.return_value = table_mock
    table_mock.delete.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.range.return_value = table_mock
    table_mock.order.return_value = table_mock
    
    # Default execute response
    table_mock.execute.return_value = mock_supabase_response([])
    
    # Return the same mock for all table() calls
    client.table.return_value = table_mock
    
    return client


@pytest.fixture
def sample_category():
    """Sample category data for testing"""
    return {
        "category_id": str(uuid4()),
        "name": "Test Category",
        "is_active": True,
        "parent_category_id": None
    }


@pytest.fixture
def sample_transaction():
    """Sample transaction data for testing"""
    return {
        "transaction_id": str(uuid4()),
        "date": datetime.now(timezone.utc).isoformat(),
        "amount": "50.00",
        "merchant": "Test Store",
        "category_id": str(uuid4()),
        "is_recurring": False,
        "notes": "Test transaction",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_tag():
    """Sample tag data for testing"""
    return {
        "tag_id": str(uuid4()),
        "value": "test_tag"
    }