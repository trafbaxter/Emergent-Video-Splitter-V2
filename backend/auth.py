from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import bcrypt
import pyotp
import qrcode
from io import BytesIO
import base64
import secrets
import os
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from models import UserInDB, UserResponse

# Security configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "4320"))

# Initialize security
security = HTTPBearer()

class AuthUtils:
    """Authentication utilities for password hashing, token generation, and 2FA"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create a JWT refresh token (3 days expiry)"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=3)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    @staticmethod
    def generate_totp_secret() -> str:
        """Generate a new TOTP secret for 2FA"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_totp_qr_code(secret: str, user_email: str, issuer: str = "Video Splitter Pro") -> str:
        """Generate a QR code for TOTP setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=issuer
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for frontend display
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
        """Verify a TOTP code"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=window)
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> list:
        """Generate backup codes for 2FA"""
        return [secrets.token_hex(4).upper() for _ in range(count)]
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)

class AuthService:
    """Authentication service for user management"""
    
    def __init__(self, db: AsyncIOMotorClient):
        self.db = db
        self.users_collection = db.users
        self.tokens_collection = db.email_tokens
        self.settings_collection = db.settings
        
        # Create indexes
        self._create_indexes()
    
    async def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # User indexes
            await self.users_collection.create_index("username", unique=True)
            await self.users_collection.create_index("email", unique=True)
            await self.users_collection.create_index("id", unique=True)
            
            # Token indexes with TTL
            await self.tokens_collection.create_index("expires_at", expireAfterSeconds=0)
            await self.tokens_collection.create_index("token", unique=True)
            
        except Exception as e:
            print(f"Index creation error (may already exist): {e}")
    
    async def create_user(self, user_data: dict) -> UserInDB:
        """Create a new user"""
        # Check if user already exists
        existing_user = await self.users_collection.find_one({
            "$or": [
                {"username": user_data["username"]},
                {"email": user_data["email"]}
            ]
        })
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username or email already exists"
            )
        
        # Hash password
        hashed_password = AuthUtils.hash_password(user_data["password"])
        
        # Create user document
        user_doc = {
            "id": user_data.get("id", str(secrets.token_urlsafe(16))),
            "username": user_data["username"],
            "email": user_data["email"],
            "name": user_data["name"],
            "role": user_data.get("role", "user"),
            "password_hash": hashed_password,
            "is_verified": False,
            "totp_secret": None,
            "is_2fa_enabled": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None,
            "failed_login_attempts": 0,
            "locked_until": None
        }
        
        # Insert user
        await self.users_collection.insert_one(user_doc)
        
        return UserInDB(**user_doc)
    
    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """Get user by username"""
        user_doc = await self.users_collection.find_one({"username": username})
        return UserInDB(**user_doc) if user_doc else None
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        user_doc = await self.users_collection.find_one({"email": email})
        return UserInDB(**user_doc) if user_doc else None
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID"""
        user_doc = await self.users_collection.find_one({"id": user_id})
        return UserInDB(**user_doc) if user_doc else None
    
    async def update_user(self, user_id: str, update_data: dict) -> Optional[UserInDB]:
        """Update user information"""
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.users_collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count:
            return await self.get_user_by_id(user_id)
        return None
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        result = await self.users_collection.delete_one({"id": user_id})
        return result.deleted_count > 0
    
    async def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with username and password"""
        user = await self.get_user_by_username(username)
        
        if not user:
            return None
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to too many failed login attempts"
            )
        
        # Verify password
        if not AuthUtils.verify_password(password, user.password_hash):
            # Increment failed attempts
            await self.increment_failed_login_attempts(user.id)
            return None
        
        # Reset failed attempts on successful login
        await self.reset_failed_login_attempts(user.id)
        
        return user
    
    async def increment_failed_login_attempts(self, user_id: str):
        """Increment failed login attempts and lock account if necessary"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return
        
        failed_attempts = user.failed_login_attempts + 1
        update_data = {"failed_login_attempts": failed_attempts}
        
        # Lock account after 5 failed attempts
        if failed_attempts >= 5:
            update_data["locked_until"] = datetime.utcnow() + timedelta(minutes=30)
        
        await self.update_user(user_id, update_data)
    
    async def reset_failed_login_attempts(self, user_id: str):
        """Reset failed login attempts"""
        await self.update_user(user_id, {
            "failed_login_attempts": 0,
            "locked_until": None,
            "last_login": datetime.utcnow()
        })
    
    async def verify_user_email(self, user_id: str):
        """Mark user email as verified"""
        await self.update_user(user_id, {"is_verified": True})
    
    async def enable_2fa(self, user_id: str, secret: str):
        """Enable 2FA for user"""
        await self.update_user(user_id, {
            "totp_secret": secret,
            "is_2fa_enabled": True
        })
    
    async def disable_2fa(self, user_id: str):
        """Disable 2FA for user"""
        await self.update_user(user_id, {
            "totp_secret": None,
            "is_2fa_enabled": False
        })
    
    async def get_system_settings(self) -> dict:
        """Get system settings"""
        settings = await self.settings_collection.find_one({"type": "system"})
        if not settings:
            default_settings = {
                "type": "system",
                "allow_user_registration": False,
                "max_failed_login_attempts": 5,
                "account_lockout_duration": 30
            }
            await self.settings_collection.insert_one(default_settings)
            return default_settings
        return settings
    
    async def update_system_settings(self, settings: dict):
        """Update system settings"""
        await self.settings_collection.update_one(
            {"type": "system"},
            {"$set": settings},
            upsert=True
        )

# Dependency for getting current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends()
) -> UserResponse:
    """Get current authenticated user"""
    try:
        # Extract token from Bearer scheme
        token = credentials.credentials
        
        # Verify token
        payload = AuthUtils.verify_token(token, "access")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get user from database
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            name=user.name,
            role=user.role,
            is_verified=user.is_verified,
            is_2fa_enabled=user.is_2fa_enabled,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

# Dependency for admin-only access
async def get_current_admin_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """Get current user and ensure they are an admin"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Dependency for verified users only
async def get_current_verified_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """Get current user and ensure they are verified"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user