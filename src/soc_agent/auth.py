"""Authentication and authorization services for SOC Agent."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import pyotp
import qrcode
from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import SETTINGS
from .database import AuditLog, Role, User, get_db

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth 2.0 provider configurations
OAUTH_PROVIDERS = {
    "google": {
        "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scope": "openid email profile",
    },
    "microsoft": {
        "authorization_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "scope": "openid email profile",
    },
    "generic": {
        "authorization_url": None,  # Must be provided via environment
        "token_url": None,  # Must be provided via environment
        "userinfo_url": None,  # Must be provided via environment
        "scope": "openid email profile",
    }
}

# Default system roles and permissions
DEFAULT_ROLES = {
    "admin": {
        "display_name": "Administrator",
        "description": "Full system access",
        "permissions": [
            "users:read", "users:create", "users:update", "users:delete",
            "roles:read", "roles:create", "roles:update", "roles:delete",
            "alerts:read", "alerts:create", "alerts:update", "alerts:delete",
            "audit:read", "settings:read", "settings:update",
            "ai:analyze", "mcp:scan", "reports:generate"
        ],
        "is_system_role": True
    },
    "analyst": {
        "display_name": "Security Analyst",
        "description": "Security analysis and alert management",
        "permissions": [
            "alerts:read", "alerts:update", "alerts:assign",
            "ai:analyze", "mcp:scan", "reports:generate"
        ],
        "is_system_role": True
    },
    "viewer": {
        "display_name": "Viewer",
        "description": "Read-only access to alerts and reports",
        "permissions": [
            "alerts:read", "reports:generate"
        ],
        "is_system_role": True
    }
}


class AuthenticationError(Exception):
    """Authentication related errors."""
    pass


class AuthorizationError(Exception):
    """Authorization related errors."""
    pass


class AuthService:
    """Authentication and authorization service."""
    
    def __init__(self):
        self.pwd_context = pwd_context
        self.oauth_providers = OAUTH_PROVIDERS
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=SETTINGS.jwt_access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SETTINGS.jwt_secret_key, algorithm=SETTINGS.jwt_algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=SETTINGS.jwt_refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SETTINGS.jwt_secret_key, algorithm=SETTINGS.jwt_algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, SETTINGS.jwt_secret_key, algorithms=[SETTINGS.jwt_algorithm])
            return payload
        except JWTError:
            raise AuthenticationError("Invalid token")
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = self.get_user_by_email(db, email)
        if not user:
            return None
        if not user.hashed_password:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user
    
    def create_user(self, db: Session, email: str, username: str, password: Optional[str] = None, 
                   full_name: Optional[str] = None, oauth_provider: Optional[str] = None,
                   oauth_id: Optional[str] = None, oauth_data: Optional[Dict] = None) -> User:
        """Create a new user."""
        # Check if user already exists
        existing_user = self.get_user_by_email(db, email)
        if existing_user:
            raise AuthenticationError("User with this email already exists")
        
        existing_username = self.get_user_by_username(db, username)
        if existing_username:
            raise AuthenticationError("User with this username already exists")
        
        # Hash password if provided
        hashed_password = None
        if password:
            hashed_password = self.get_password_hash(password)
        
        # Create user
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=hashed_password,
            oauth_provider=oauth_provider,
            oauth_id=oauth_id,
            oauth_data=oauth_data or {},
            is_verified=oauth_provider is not None,  # OAuth users are pre-verified
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Assign default role
        self.assign_default_role(db, user)
        
        return user
    
    def assign_default_role(self, db: Session, user: User) -> None:
        """Assign default role to user."""
        default_role = db.query(Role).filter(Role.name == SETTINGS.default_user_role).first()
        if default_role:
            user.roles.append(default_role)
            db.commit()
    
    def get_user_roles(self, db: Session, user: User) -> List[Role]:
        """Get user roles."""
        return user.roles
    
    def get_user_permissions(self, db: Session, user: User) -> List[str]:
        """Get all permissions for a user."""
        permissions = set()
        for role in user.roles:
            if role.is_active:
                permissions.update(role.permissions)
        return list(permissions)
    
    def has_permission(self, db: Session, user: User, permission: str) -> bool:
        """Check if user has specific permission."""
        user_permissions = self.get_user_permissions(db, user)
        return permission in user_permissions
    
    def check_permission(self, db: Session, user: User, permission: str) -> None:
        """Check permission and raise exception if not granted."""
        if not self.has_permission(db, user, permission):
            raise AuthorizationError(f"Permission denied: {permission}")
    
    def setup_mfa(self, db: Session, user: User) -> Dict[str, Any]:
        """Setup MFA for user."""
        if user.mfa_enabled:
            raise AuthenticationError("MFA already enabled for this user")
        
        # Generate TOTP secret
        secret = pyotp.random_base32()
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(SETTINGS.mfa_backup_codes_count)]
        
        # Update user
        user.mfa_secret = secret
        user.mfa_backup_codes = backup_codes
        db.commit()
        
        # Generate QR code
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name=SETTINGS.mfa_issuer_name
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        return {
            "secret": secret,
            "backup_codes": backup_codes,
            "qr_code_uri": totp_uri,
            "qr_code": qr.make_image(fill_color="black", back_color="white")
        }
    
    def enable_mfa(self, db: Session, user: User, totp_code: str) -> bool:
        """Enable MFA for user after verification."""
        if not user.mfa_secret:
            raise AuthenticationError("MFA not set up for this user")
        
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(totp_code, valid_window=1):
            return False
        
        user.mfa_enabled = True
        db.commit()
        return True
    
    def verify_mfa(self, user: User, totp_code: str) -> bool:
        """Verify MFA code."""
        if not user.mfa_enabled or not user.mfa_secret:
            return False
        
        totp = pyotp.TOTP(user.mfa_secret)
        return totp.verify(totp_code, valid_window=1)
    
    def verify_backup_code(self, user: User, backup_code: str) -> bool:
        """Verify MFA backup code."""
        if not user.mfa_enabled or not user.mfa_backup_codes:
            return False
        
        if backup_code.upper() in user.mfa_backup_codes:
            # Remove used backup code
            user.mfa_backup_codes.remove(backup_code.upper())
            return True
        return False
    
    def get_oauth_authorization_url(self, provider: str, state: str) -> str:
        """Get OAuth authorization URL."""
        if provider not in self.oauth_providers:
            raise AuthenticationError(f"Unsupported OAuth provider: {provider}")
        
        provider_config = self.oauth_providers[provider]
        if provider == "generic":
            # Use custom URLs from settings
            auth_url = SETTINGS.oauth_authorization_url
            if not auth_url:
                raise AuthenticationError("Generic OAuth provider requires custom authorization URL")
        else:
            auth_url = provider_config["authorization_url"]
        
        params = {
            "client_id": SETTINGS.oauth_client_id,
            "redirect_uri": SETTINGS.oauth_redirect_uri,
            "scope": provider_config["scope"],
            "response_type": "code",
            "state": state,
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{auth_url}?{query_string}"
    
    def exchange_oauth_code(self, provider: str, code: str) -> Dict[str, Any]:
        """Exchange OAuth authorization code for tokens."""
        import requests
        
        if provider not in self.oauth_providers:
            raise AuthenticationError(f"Unsupported OAuth provider: {provider}")
        
        provider_config = self.oauth_providers[provider]
        if provider == "generic":
            token_url = SETTINGS.oauth_token_url
            if not token_url:
                raise AuthenticationError("Generic OAuth provider requires custom token URL")
        else:
            token_url = provider_config["token_url"]
        
        data = {
            "client_id": SETTINGS.oauth_client_id,
            "client_secret": SETTINGS.oauth_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": SETTINGS.oauth_redirect_uri,
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        return response.json()
    
    def get_oauth_user_info(self, provider: str, access_token: str) -> Dict[str, Any]:
        """Get user info from OAuth provider."""
        import requests
        
        if provider not in self.oauth_providers:
            raise AuthenticationError(f"Unsupported OAuth provider: {provider}")
        
        provider_config = self.oauth_providers[provider]
        if provider == "generic":
            userinfo_url = SETTINGS.oauth_userinfo_url
            if not userinfo_url:
                raise AuthenticationError("Generic OAuth provider requires custom userinfo URL")
        else:
            userinfo_url = provider_config["userinfo_url"]
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(userinfo_url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def log_audit_event(self, db: Session, user: Optional[User], event_type: str, 
                       event_category: str, action: str, description: Optional[str] = None,
                       resource_type: Optional[str] = None, resource_id: Optional[str] = None,
                       details: Optional[Dict] = None, success: bool = True,
                       request: Optional[Request] = None) -> None:
        """Log audit event."""
        audit_log = AuditLog(
            user_id=user.id if user else None,
            session_id=str(uuid.uuid4()),  # Generate session ID
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            event_type=event_type,
            event_category=event_category,
            action=action,
            description=description,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            success=success,
            risk_level="LOW",  # Default risk level
            compliance_tags=["AUTH"],  # Default compliance tag
            data_classification="internal",  # Default data classification
        )
        
        db.add(audit_log)
        db.commit()


# Global auth service instance
auth_service = AuthService()


def create_default_roles(db: Session) -> None:
    """Create default system roles."""
    for role_name, role_data in DEFAULT_ROLES.items():
        existing_role = db.query(Role).filter(Role.name == role_name).first()
        if not existing_role:
            role = Role(
                name=role_name,
                display_name=role_data["display_name"],
                description=role_data["description"],
                permissions=role_data["permissions"],
                is_system_role=role_data["is_system_role"]
            )
            db.add(role)
    
    db.commit()


def get_current_user(db: Session, token: str) -> User:
    """Get current user from JWT token."""
    try:
        payload = auth_service.verify_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid token payload")
        
        user = auth_service.get_user_by_id(db, int(user_id))
        if user is None:
            raise AuthenticationError("User not found")
        
        return user
    except (JWTError, ValueError):
        raise AuthenticationError("Invalid token")


def require_permission(permission: str):
    """Decorator to require specific permission."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be implemented in the API layer
            # where we have access to the current user and database
            pass
        return wrapper
    return decorator
