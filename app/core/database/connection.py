from supabase import create_client, Client
from app.shared.config import get_settings
import os

settings = get_settings()

# Safety check: Never use real DB in test environment
if settings.environment == "test":
    # In test environment, create a mock client that fails on actual operations
    class MockSupabaseClient:
        def table(self, table_name):
            raise RuntimeError(
                f"DANGER: Attempted to access table '{table_name}' in test environment! "
                "Tests must mock 'app.database.supabase'. "
                "Use: @patch('app.database.supabase', mock_supabase_client)"
            )
        
        def __getattr__(self, name):
            raise RuntimeError(
                f"DANGER: Attempted to use Supabase method '{name}' in test environment! "
                "Tests must mock 'app.database.supabase'."
            )
    
    supabase = MockSupabaseClient()
else:
    # Production/development environment
    if not settings.effective_supabase_url or not settings.effective_supabase_key:
        raise ValueError("Supabase URL and key must be configured for non-test environments")
    
    supabase = create_client(settings.effective_supabase_url, settings.effective_supabase_key)