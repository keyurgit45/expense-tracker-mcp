"""
Authentication models for JWT with Supabase
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class UserInfo(BaseModel):
    """User information from JWT token"""
    id: str = Field(..., description="User ID from Supabase")
    email: Optional[str] = Field(None, description="User email")
    role: Optional[str] = Field(None, description="User role")
    aud: Optional[str] = Field(None, description="Audience")
    exp: Optional[int] = Field(None, description="Expiration timestamp")
    iat: Optional[int] = Field(None, description="Issued at timestamp")
    iss: Optional[str] = Field(None, description="Issuer")
    sub: Optional[str] = Field(None, description="Subject")


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token")


class LoginRequest(BaseModel):
    """Login request model"""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str = Field(..., description="Refresh token")


class AuthError(BaseModel):
    """Authentication error response"""
    error: str = Field(..., description="Error message")
    error_description: Optional[str] = Field(None, description="Detailed error description") 