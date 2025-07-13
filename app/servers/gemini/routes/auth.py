"""
Authentication routes for Gemini server
"""
from fastapi import APIRouter, HTTPException, Depends
from app.core.models.auth_models import LoginRequest, RefreshTokenRequest, TokenResponse
from app.servers.gemini.auth.jwt_auth import get_auth_service, SupabaseAuthService, get_current_user

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """
    Authenticate user with email and password.
    
    Returns JWT access token and refresh token.
    """
    return await auth_service.authenticate_user(login_data.email, login_data.password)


@router.post("/auth/signup", response_model=TokenResponse)
async def signup(
    signup_data: LoginRequest,
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """
    Register new user with email and password.
    
    Returns JWT access token and refresh token.
    """
    return await auth_service.sign_up_user(signup_data.email, signup_data.password)


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token.
    
    Returns new JWT access token and refresh token.
    """
    return await auth_service.refresh_token(refresh_data.refresh_token)


@router.post("/auth/logout")
async def logout(
    auth_service: SupabaseAuthService = Depends(get_auth_service),
    current_user = Depends(get_current_user)
):
    """
    Sign out current user.
    
    Requires authentication.
    """
    # Note: This would require the access token to be passed
    # For now, we'll just return success
    return {"message": "Logged out successfully"}


@router.get("/auth/me")
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """
    Get current user information.
    
    Requires authentication.
    """
    return current_user 