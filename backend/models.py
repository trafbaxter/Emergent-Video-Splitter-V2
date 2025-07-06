from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import re

# User Models
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(default="user")  # "admin" or "user"
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['admin', 'user']:
            raise ValueError('Role must be either "admin" or "user"')
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=14)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 14:
            raise ValueError('Password must be at least 14 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    
    @validator('role')
    def validate_role(cls, v):
        if v is not None and v not in ['admin', 'user']:
            raise ValueError('Role must be either "admin" or "user"')
        return v

class UserInDB(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    password_hash: str
    is_verified: bool = False
    totp_secret: Optional[str] = None
    is_2fa_enabled: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None

class UserResponse(UserBase):
    id: str
    is_verified: bool
    is_2fa_enabled: bool
    created_at: datetime
    last_login: Optional[datetime]

# Authentication Models
class LoginRequest(BaseModel):
    username: str
    password: str
    totp_code: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

# Email Models
class EmailVerificationRequest(BaseModel):
    user_id: str
    
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 14:
            raise ValueError('Password must be at least 14 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v

# 2FA Models
class TwoFactorSetupResponse(BaseModel):
    qr_code_url: str
    secret_key: str
    backup_codes: List[str]

class TwoFactorVerifyRequest(BaseModel):
    totp_code: str

class TwoFactorToggleRequest(BaseModel):
    totp_code: str
    enable: bool

# Admin Models
class AdminUserCreate(UserCreate):
    role: str = Field(default="user")

class AdminUserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    password: Optional[str] = None
    is_verified: Optional[bool] = None
    is_2fa_enabled: Optional[bool] = None
    
    @validator('role')
    def validate_role(cls, v):
        if v is not None and v not in ['admin', 'user']:
            raise ValueError('Role must be either "admin" or "user"')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None:
            if len(v) < 14:
                raise ValueError('Password must be at least 14 characters long')
            
            if not re.search(r'[A-Z]', v):
                raise ValueError('Password must contain at least one uppercase letter')
            
            if not re.search(r'[a-z]', v):
                raise ValueError('Password must contain at least one lowercase letter')
            
            if not re.search(r'\d', v):
                raise ValueError('Password must contain at least one number')
            
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
                raise ValueError('Password must contain at least one special character')
        
        return v

class AdminUserResponse(UserResponse):
    failed_login_attempts: int
    locked_until: Optional[datetime]

# System Models
class SystemSettings(BaseModel):
    allow_user_registration: bool = False
    max_failed_login_attempts: int = 5
    account_lockout_duration: int = 30  # minutes
    
class UploadHistoryItem(BaseModel):
    job_id: str
    filename: str
    original_size: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    splits_count: int = 0

class UserUploadHistory(BaseModel):
    user_id: str
    uploads: List[UploadHistoryItem]
    total_uploads: int
    total_size: int