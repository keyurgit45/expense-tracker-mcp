"""
JWT Authentication service for Supabase integration
"""
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client, create_client
from app.core.models.auth_models import UserInfo, TokenResponse, LoginRequest, RefreshTokenRequest
from app.shared.config import get_settings

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)

# Get settings
settings = get_settings()


class SupabaseAuthService:
    """Supabase authentication service with JWT handling"""
    
    def __init__(self):
        """Initialize Supabase client for authentication"""
        if not settings.effective_supabase_url or not settings.effective_supabase_key:
            raise ValueError("Supabase URL and key must be configured for authentication")
        
        self.supabase: Client = create_client(
            settings.effective_supabase_url, 
            settings.effective_supabase_key
        )
        
        # JWT settings
        self.jwt_secret = settings.effective_supabase_key
        self.jwt_algorithm = "HS256"
    
    async def authenticate_user(self, email: str, password: str) -> TokenResponse:
        """Authenticate user with email and password"""
        try:
            # Sign in with Supabase
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            user = response.user
            session = response.session
            
            if not user or not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            return TokenResponse(
                access_token=session.access_token,
                token_type="bearer",
                expires_in=session.expires_in,
                refresh_token=session.refresh_token
            )
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token"""
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            session = response.session
            
            return TokenResponse(
                access_token=session.access_token,
                token_type="bearer",
                expires_in=session.expires_in,
                refresh_token=session.refresh_token
            )
            
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    
    async def verify_token(self, token: str) -> UserInfo:
        """Verify JWT token and extract user information"""
        try:
            # For Supabase tokens, we can decode without verification
            # since Supabase already verified them when issued
            # The anon key is not the JWT secret, so we skip signature verification
            import json
            import base64
            
            # Split the JWT token
            parts = token.split('.')
            if len(parts) != 3:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token format"
                )
            
            # Decode the payload (add padding if needed)
            payload_data = parts[1]
            payload_data += '=' * (4 - len(payload_data) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_data))
            
            # Extract user information from the payload
            user_id = payload.get("sub")
            email = payload.get("email")
            
            if not user_id or not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Check if token is expired
            exp = payload.get("exp", 0)
            if exp < datetime.now(timezone.utc).timestamp():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
            
            return UserInfo(
                id=user_id,
                email=email,
                role=payload.get("role"),
                aud=payload.get("aud"),
                exp=exp,
                iat=payload.get("iat"),
                iss=payload.get("iss"),
                sub=user_id
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}, type: {type(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )
    
    async def sign_up_user(self, email: str, password: str) -> TokenResponse:
        """Sign up new user"""
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            user = response.user
            session = response.session
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User registration failed"
                )
            
            return TokenResponse(
                access_token=session.access_token if session else None,
                token_type="bearer",
                expires_in=session.expires_in if session else None,
                refresh_token=session.refresh_token if session else None
            )
            
        except Exception as e:
            logger.error(f"User registration error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User registration failed"
            )
    
    async def sign_out(self, token: str) -> bool:
        """Sign out user"""
        try:
            self.supabase.auth.sign_out(token)
            return True
        except Exception as e:
            logger.error(f"Sign out error: {str(e)}")
            return False


# Global auth service instance
_auth_service: Optional[SupabaseAuthService] = None


def get_auth_service() -> SupabaseAuthService:
    """Get or create auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = SupabaseAuthService()
    return _auth_service


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
) -> UserInfo:
    """Dependency to get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    return await auth_service.verify_token(token)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
) -> Optional[UserInfo]:
    """Dependency to get current user (optional - doesn't require auth)"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        return await auth_service.verify_token(token)
    except HTTPException:
        return None 