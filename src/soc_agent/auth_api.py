"""Authentication API endpoints for SOC Agent."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .auth import AuthenticationError, AuthorizationError, auth_service, get_current_user
from .config import SETTINGS
from .database import AuditLog, Role, User, get_db

# Security scheme
security = HTTPBearer()

# API router
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


# Pydantic models for request/response
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_code: Optional[str] = None


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str
    provider: str = "google"


class MfaSetupRequest(BaseModel):
    totp_code: str


class MfaVerifyRequest(BaseModel):
    mfa_code: str


class UserCreateRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    oauth_provider: Optional[str]
    mfa_enabled: bool
    avatar_url: Optional[str]
    department: Optional[str]
    job_title: Optional[str]
    created_at: datetime
    updated_at: datetime
    roles: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class MfaSetupResponse(BaseModel):
    qr_code_uri: str
    backup_codes: List[str]
    secret: str


class OAuthUrlResponse(BaseModel):
    authorization_url: str
    state: str


# Dependency to get current user
async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    try:
        return get_current_user(db, credentials.credentials)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# Authentication endpoints
@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user with email and password."""
    try:
        # Authenticate user
        user = auth_service.authenticate_user(db, login_data.email, login_data.password)
        if not user:
            auth_service.log_audit_event(
                db, None, "login", "auth", "login_attempt", 
                f"Failed login attempt for {login_data.email}",
                success=False, request=request
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check MFA if enabled
        if user.mfa_enabled:
            if not login_data.mfa_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="MFA code required"
                )
            
            if not auth_service.verify_mfa(user, login_data.mfa_code):
                auth_service.log_audit_event(
                    db, user, "login", "auth", "mfa_verification_failed",
                    f"MFA verification failed for {user.email}",
                    success=False, request=request
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid MFA code"
                )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create tokens
        access_token = auth_service.create_access_token({"sub": str(user.id)})
        refresh_token = auth_service.create_refresh_token({"sub": str(user.id)})
        
        # Log successful login
        auth_service.log_audit_event(
            db, user, "login", "auth", "login_success",
            f"Successful login for {user.email}",
            success=True, request=request
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=SETTINGS.jwt_access_token_expire_minutes * 60,
            user=UserResponse(
                **user.to_dict(),
                roles=[role.to_dict() for role in user.roles]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        auth_service.log_audit_event(
            db, None, "login", "auth", "login_error",
            f"Login error: {str(e)}",
            success=False, request=request
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/register", response_model=UserResponse)
async def register(
    request: Request,
    user_data: UserCreateRequest,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    try:
        user = auth_service.create_user(
            db, user_data.email, user_data.username, user_data.password, user_data.full_name
        )
        
        # Log user creation
        auth_service.log_audit_event(
            db, user, "create", "auth", "user_registration",
            f"User registered: {user.email}",
            resource_type="user", resource_id=str(user.id),
            success=True, request=request
        )
        
        return UserResponse(
            **user.to_dict(),
            roles=[role.to_dict() for role in user.roles]
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        auth_service.log_audit_event(
            db, None, "create", "auth", "user_registration_error",
            f"Registration error: {str(e)}",
            success=False, request=request
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    try:
        payload = auth_service.verify_token(refresh_token)
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")
        
        user_id = payload.get("sub")
        user = auth_service.get_user_by_id(db, int(user_id))
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        
        # Create new tokens
        access_token = auth_service.create_access_token({"sub": str(user.id)})
        new_refresh_token = auth_service.create_refresh_token({"sub": str(user.id)})
        
        # Log token refresh
        auth_service.log_audit_event(
            db, user, "update", "auth", "token_refresh",
            f"Token refreshed for {user.email}",
            success=True, request=request
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=SETTINGS.jwt_access_token_expire_minutes * 60,
            user=UserResponse(
                **user.to_dict(),
                roles=[role.to_dict() for role in user.roles]
            )
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user_dependency)
):
    """Get current user information."""
    return UserResponse(
        **current_user.to_dict(),
        roles=[role.to_dict() for role in current_user.roles]
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Logout current user."""
    # Log logout
    auth_service.log_audit_event(
        db, current_user, "logout", "auth", "logout",
        f"User logged out: {current_user.email}",
        success=True, request=request
    )
    
    return {"message": "Successfully logged out"}


# OAuth 2.0 endpoints
@router.get("/oauth/{provider}/url", response_model=OAuthUrlResponse)
async def get_oauth_url(provider: str):
    """Get OAuth authorization URL."""
    if not SETTINGS.oauth_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth is not enabled"
        )
    
    state = str(uuid.uuid4())
    try:
        authorization_url = auth_service.get_oauth_authorization_url(provider, state)
        return OAuthUrlResponse(
            authorization_url=authorization_url,
            state=state
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/oauth/callback", response_model=TokenResponse)
async def oauth_callback(
    request: Request,
    callback_data: OAuthCallbackRequest,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback."""
    if not SETTINGS.oauth_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth is not enabled"
        )
    
    try:
        # Exchange code for tokens
        token_data = auth_service.exchange_oauth_code(callback_data.provider, callback_data.code)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise AuthenticationError("No access token received")
        
        # Get user info
        user_info = auth_service.get_oauth_user_info(callback_data.provider, access_token)
        
        # Extract user data
        email = user_info.get("email")
        if not email:
            raise AuthenticationError("No email in OAuth response")
        
        username = user_info.get("preferred_username") or user_info.get("name", "").replace(" ", "_").lower()
        full_name = user_info.get("name")
        avatar_url = user_info.get("picture")
        
        # Check if user exists
        user = auth_service.get_user_by_email(db, email)
        if not user:
            # Create new user
            user = auth_service.create_user(
                db, email, username, None, full_name,
                callback_data.provider, user_info.get("id"), user_info
            )
            user.avatar_url = avatar_url
            db.commit()
        else:
            # Update existing user
            user.oauth_provider = callback_data.provider
            user.oauth_id = user_info.get("id")
            user.oauth_data = user_info
            user.avatar_url = avatar_url
            user.last_login = datetime.utcnow()
            db.commit()
        
        # Create our tokens
        our_access_token = auth_service.create_access_token({"sub": str(user.id)})
        our_refresh_token = auth_service.create_refresh_token({"sub": str(user.id)})
        
        # Log OAuth login
        auth_service.log_audit_event(
            db, user, "login", "auth", "oauth_login",
            f"OAuth login via {callback_data.provider} for {user.email}",
            success=True, request=request
        )
        
        return TokenResponse(
            access_token=our_access_token,
            refresh_token=our_refresh_token,
            expires_in=SETTINGS.jwt_access_token_expire_minutes * 60,
            user=UserResponse(
                **user.to_dict(),
                roles=[role.to_dict() for role in user.roles]
            )
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        auth_service.log_audit_event(
            db, None, "login", "auth", "oauth_error",
            f"OAuth error: {str(e)}",
            success=False, request=request
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# MFA endpoints
@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def setup_mfa(
    request: Request,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Setup MFA for current user."""
    if not SETTINGS.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled"
        )
    
    try:
        mfa_data = auth_service.setup_mfa(db, current_user)
        
        # Log MFA setup
        auth_service.log_audit_event(
            db, current_user, "update", "auth", "mfa_setup",
            f"MFA setup initiated for {current_user.email}",
            success=True, request=request
        )
        
        return MfaSetupResponse(
            qr_code_uri=mfa_data["qr_code_uri"],
            backup_codes=mfa_data["backup_codes"],
            secret=mfa_data["secret"]
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/mfa/enable")
async def enable_mfa(
    request: Request,
    mfa_data: MfaSetupRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Enable MFA after verification."""
    if not SETTINGS.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled"
        )
    
    try:
        success = auth_service.enable_mfa(db, current_user, mfa_data.totp_code)
        if not success:
            auth_service.log_audit_event(
                db, current_user, "update", "auth", "mfa_enable_failed",
                f"MFA enable failed for {current_user.email}",
                success=False, request=request
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA code"
            )
        
        # Log MFA enable
        auth_service.log_audit_event(
            db, current_user, "update", "auth", "mfa_enabled",
            f"MFA enabled for {current_user.email}",
            success=True, request=request
        )
        
        return {"message": "MFA enabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        auth_service.log_audit_event(
            db, current_user, "update", "auth", "mfa_enable_error",
            f"MFA enable error: {str(e)}",
            success=False, request=request
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/mfa/disable")
async def disable_mfa(
    request: Request,
    mfa_data: MfaVerifyRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Disable MFA for current user."""
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this user"
        )
    
    try:
        # Verify MFA code
        if not auth_service.verify_mfa(current_user, mfa_data.mfa_code):
            auth_service.log_audit_event(
                db, current_user, "update", "auth", "mfa_disable_failed",
                f"MFA disable failed for {current_user.email}",
                success=False, request=request
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA code"
            )
        
        # Disable MFA
        current_user.mfa_enabled = False
        current_user.mfa_secret = None
        current_user.mfa_backup_codes = []
        db.commit()
        
        # Log MFA disable
        auth_service.log_audit_event(
            db, current_user, "update", "auth", "mfa_disabled",
            f"MFA disabled for {current_user.email}",
            success=True, request=request
        )
        
        return {"message": "MFA disabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        auth_service.log_audit_event(
            db, current_user, "update", "auth", "mfa_disable_error",
            f"MFA disable error: {str(e)}",
            success=False, request=request
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Role and permission endpoints
@router.get("/roles", response_model=List[Dict[str, Any]])
async def get_roles(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get all roles (admin only)."""
    auth_service.check_permission(db, current_user, "roles:read")
    
    roles = db.query(Role).filter(Role.is_active == True).all()
    return [role.to_dict() for role in roles]


@router.get("/permissions", response_model=List[str])
async def get_user_permissions(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get current user's permissions."""
    permissions = auth_service.get_user_permissions(db, current_user)
    return permissions
