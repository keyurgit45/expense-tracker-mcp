from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    environment: str = "development"
    
    # Test environment settings
    test_supabase_url: str = ""
    test_supabase_key: str = ""
    
    model_config = {"env_file": ".env"}
    
    @property
    def effective_supabase_url(self) -> str:
        """Get the appropriate Supabase URL based on environment"""
        if self.environment == "test":
            return self.test_supabase_url or "mock://test-db"
        return self.supabase_url
    
    @property  
    def effective_supabase_key(self) -> str:
        """Get the appropriate Supabase key based on environment"""
        if self.environment == "test":
            return self.test_supabase_key or "mock-test-key"
        return self.supabase_key


@lru_cache()
def get_settings():
    return Settings()