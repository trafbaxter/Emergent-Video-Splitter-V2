from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from fastapi.security import HTTPBearer
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from typing import List, Optional
import os

from backend.models import (
    LoginRequest, LoginResponse, TokenRefreshRequest, TokenResponse,
    UserCreate, UserResponse, UserUpdate, EmailVerificationRequest,
    PasswordResetRequest, PasswordResetConfirm, TwoFactorSetupResponse,
    TwoFactorVerifyRequest, TwoFactorToggleRequest, AdminUserCreate,
    AdminUserUpdate, AdminUserResponse, SystemSettings, UploadHistoryItem,
    UserUploadHistory
)
from backend.auth import (
    AuthService, AuthUtils, get_current_user, get_current_admin_user,
    get_current_verified_user
)
from backend.email_service import EmailService, get_email_service

# Initialize router
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])

# Initialize security
security = HTTPBearer()

def get_db():
    """Get database connection (this will be replaced with actual DB dependency)"""
    # This is a placeholder - will be replaced with actual DB connection
    pass

def get_auth_service(db = Depends(get_db)):
    """Get authentication service instance"""
    return AuthService(db)

def get_email_service_dep(db = Depends(get_db)):
    """Get email service instance"""
    return get_email_service(db)

# Authentication Endpoints
@auth_router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_service = Depends(get_auth_service)
):
    """Login user with username/password and optional 2FA"""
    
    # Authenticate user
    user = await auth_service.authenticate_user(request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if user is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address before logging in"
        )
    
    # Check 2FA if enabled
    if user.is_2fa_enabled:
        if not request.totp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA code required"
            )
        
        if not AuthUtils.verify_totp_code(user.totp_secret, request.totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code"
            )
    
    # Generate tokens
    token_data = {"sub": user.id, "username": user.username, "role": user.role}
    access_token = AuthUtils.create_access_token(token_data)
    refresh_token = AuthUtils.create_refresh_token(token_data)
    
    # Update last login
    await auth_service.update_user(user.id, {"last_login": datetime.utcnow()})
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "4320")) * 60,
        user=UserResponse(
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
    )

@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    auth_service = Depends(get_auth_service)
):
    """Refresh access token using refresh token"""
    
    # Verify refresh token
    payload = AuthUtils.verify_token(request.refresh_token, "refresh")
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user to ensure they still exist
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Generate new tokens
    token_data = {"sub": user.id, "username": user.username, "role": user.role}
    new_access_token = AuthUtils.create_access_token(token_data)
    new_refresh_token = AuthUtils.create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "4320")) * 60
    )

@auth_router.post("/register", response_model=UserResponse)
async def register(
    request: UserCreate,
    background_tasks: BackgroundTasks,
    auth_service = Depends(get_auth_service),
    email_service = Depends(get_email_service_dep)
):
    """Register a new user (admin only, unless public registration is enabled)"""
    
    # Check if public registration is allowed
    settings = await auth_service.get_system_settings()
    if not settings.get("allow_user_registration", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration is disabled. Please contact an administrator."
        )
    
    # Create user
    user_data = request.dict()
    user = await auth_service.create_user(user_data)
    
    # Send verification email
    background_tasks.add_task(
        email_service.send_verification_email,
        user.email,
        user.name,
        user.id
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

@auth_router.post("/verify-email")
async def verify_email(
    token: str,
    db: AsyncIOMotorClient = Depends(get_db)
):
    """Verify user email address"""
    auth_service = get_auth_service(db)
    email_service = get_email_service(db)
    
    # Verify token
    result = await email_service.verify_token(token, "verification")
    
    if not result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    # Mark user as verified
    user = await auth_service.get_user_by_id(result["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await auth_service.verify_user_email(user.id)
    
    # Send welcome email
    await email_service.send_welcome_email(user.email, user.name)
    
    return {"message": "Email verified successfully"}

@auth_router.post("/forgot-password")
async def forgot_password(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorClient = Depends(get_db)
):
    """Send password reset email"""
    auth_service = get_auth_service(db)
    email_service = get_email_service(db)
    
    # Find user by email
    user = await auth_service.get_user_by_email(request.email)
    
    if user:
        # Send password reset email
        background_tasks.add_task(
            email_service.send_password_reset_email,
            user.email,
            user.name,
            user.id
        )
    
    # Always return success to prevent email enumeration
    return {"message": "If an account with this email exists, a password reset link has been sent."}

@auth_router.post("/reset-password")
async def reset_password(
    request: PasswordResetConfirm,
    db: AsyncIOMotorClient = Depends(get_db)
):
    """Reset password using token"""
    auth_service = get_auth_service(db)
    email_service = get_email_service(db)
    
    # Verify token
    result = await email_service.verify_token(request.token, "password_reset")
    
    if not result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    # Update user password
    hashed_password = AuthUtils.hash_password(request.new_password)
    await auth_service.update_user(result["user_id"], {
        "password_hash": hashed_password,
        "failed_login_attempts": 0,
        "locked_until": None
    })
    
    return {"message": "Password reset successfully"}

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@auth_router.put("/me", response_model=UserResponse)
async def update_current_user(
    request: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorClient = Depends(get_db)
):
    """Update current user information"""
    auth_service = get_auth_service(db)
    
    # Update user
    update_data = request.dict(exclude_unset=True)
    updated_user = await auth_service.update_user(current_user.id, update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        name=updated_user.name,
        role=updated_user.role,
        is_verified=updated_user.is_verified,
        is_2fa_enabled=updated_user.is_2fa_enabled,
        created_at=updated_user.created_at,
        last_login=updated_user.last_login
    )

# 2FA Endpoints
@auth_router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    current_user: UserResponse = Depends(get_current_verified_user),
    db: AsyncIOMotorClient = Depends(get_db)
):
    """Setup 2FA for current user"""
    auth_service = get_auth_service(db)
    
    # Generate TOTP secret
    secret = AuthUtils.generate_totp_secret()
    
    # Generate QR code
    qr_code_url = AuthUtils.generate_totp_qr_code(secret, current_user.email)
    
    # Generate backup codes
    backup_codes = AuthUtils.generate_backup_codes()
    
    # Store secret temporarily (will be confirmed when user verifies)
    await auth_service.update_user(current_user.id, {"totp_secret": secret})
    
    return TwoFactorSetupResponse(
        qr_code_url=qr_code_url,
        secret_key=secret,
        backup_codes=backup_codes
    )

@auth_router.post("/2fa/verify")
async def verify_2fa_setup(
    request: TwoFactorVerifyRequest,
    current_user: UserResponse = Depends(get_current_verified_user),
    db: AsyncIOMotorClient = Depends(get_db)
):
    """Verify 2FA setup"""
    auth_service = get_auth_service(db)
    
    # Get user to check secret
    user = await auth_service.get_user_by_id(current_user.id)
    if not user or not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated"
        )
    
    # Verify TOTP code
    if not AuthUtils.verify_totp_code(user.totp_secret, request.totp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA code"
        )
    
    # Enable 2FA
    await auth_service.enable_2fa(current_user.id, user.totp_secret)
    
    return {"message": "2FA enabled successfully"}

@auth_router.post("/2fa/toggle")
async def toggle_2fa(
    request: TwoFactorToggleRequest,
    current_user: UserResponse = Depends(get_current_verified_user),
    db: AsyncIOMotorClient = Depends(get_db)
):
    """Enable or disable 2FA"""
    auth_service = get_auth_service(db)
    
    # Get user to check current 2FA status
    user = await auth_service.get_user_by_id(current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if request.enable:
        if user.is_2fa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is already enabled"
            )
        
        if not user.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA setup not completed"
            )
        
        # Verify TOTP code
        if not AuthUtils.verify_totp_code(user.totp_secret, request.totp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 2FA code"
            )
        
        await auth_service.enable_2fa(current_user.id, user.totp_secret)
        return {"message": "2FA enabled successfully"}
    
    else:
        if not user.is_2fa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is not enabled"
            )
        
        # Verify TOTP code before disabling
        if not AuthUtils.verify_totp_code(user.totp_secret, request.totp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 2FA code"
            )
        
        await auth_service.disable_2fa(current_user.id)
        return {"message": "2FA disabled successfully"}

# Upload History Endpoints
@auth_router.get("/upload-history", response_model=UserUploadHistory)
async def get_upload_history(
    current_user: UserResponse = Depends(get_current_verified_user),
    db: AsyncIOMotorClient = Depends(get_db)
):
    """Get user's upload history"""
    # Get user's video jobs
    jobs = await db.video_jobs.find({"user_id": current_user.id}).to_list(length=None)
    
    uploads = []
    total_size = 0
    
    for job in jobs:
        upload_item = UploadHistoryItem(
            job_id=job["id"],
            filename=job["filename"],
            original_size=job["original_size"],
            status=job["status"],
            created_at=job["created_at"],
            completed_at=job.get("updated_at") if job["status"] == "completed" else None,
            splits_count=len(job.get("splits", []))
        )
        uploads.append(upload_item)
        total_size += job["original_size"]
    
    return UserUploadHistory(
        user_id=current_user.id,
        uploads=uploads,
        total_uploads=len(uploads),
        total_size=total_size
    )

# Admin Endpoints
@admin_router.get("/users", response_model=List[AdminUserResponse])
async def list_users(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncIOMotorClient = Depends(get_db)
):
    """List all users (admin only)"""
    auth_service = get_auth_service(db)
    
    # Get all users
    users = await auth_service.users_collection.find({}).to_list(length=None)
    
    return [
        AdminUserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            name=user["name"],
            role=user["role"],
            is_verified=user["is_verified"],
            is_2fa_enabled=user["is_2fa_enabled"],
            created_at=user["created_at"],
            last_login=user.get("last_login"),
            failed_login_attempts=user.get("failed_login_attempts", 0),
            locked_until=user.get("locked_until")
        )
        for user in users
    ]

@admin_router.post("/users", response_model=AdminUserResponse)
async def create_user_admin(
    request: AdminUserCreate,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncIOMotorClient = Depends(get_db)
):
    """Create new user (admin only)"""
    auth_service = get_auth_service(db)
    email_service = get_email_service(db)
    
    # Create user
    user_data = request.dict()
    user = await auth_service.create_user(user_data)
    
    # Send verification email
    background_tasks.add_task(
        email_service.send_verification_email,
        user.email,
        user.name,
        user.id
    )
    
    return AdminUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        name=user.name,
        role=user.role,
        is_verified=user.is_verified,
        is_2fa_enabled=user.is_2fa_enabled,
        created_at=user.created_at,
        last_login=user.last_login,
        failed_login_attempts=user.failed_login_attempts,
        locked_until=user.locked_until
    )

@admin_router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_user_admin(
    user_id: str,
    request: AdminUserUpdate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncIOMotorClient = Depends(get_db)
):
    """Update user (admin only)"""
    auth_service = get_auth_service(db)
    
    # Prepare update data
    update_data = request.dict(exclude_unset=True)
    
    # Hash password if provided
    if "password" in update_data:
        update_data["password_hash"] = AuthUtils.hash_password(update_data["password"])
        del update_data["password"]
    
    # Update user
    updated_user = await auth_service.update_user(user_id, update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return AdminUserResponse(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        name=updated_user.name,
        role=updated_user.role,
        is_verified=updated_user.is_verified,
        is_2fa_enabled=updated_user.is_2fa_enabled,
        created_at=updated_user.created_at,
        last_login=updated_user.last_login,
        failed_login_attempts=updated_user.failed_login_attempts,
        locked_until=updated_user.locked_until
    )

@admin_router.delete("/users/{user_id}")
async def delete_user_admin(
    user_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncIOMotorClient = Depends(get_db)
):
    """Delete user (admin only)"""
    auth_service = get_auth_service(db)
    
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Delete user
    deleted = await auth_service.delete_user(user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Also delete user's uploads
    await db.video_jobs.delete_many({"user_id": user_id})
    
    return {"message": "User deleted successfully"}

@admin_router.get("/uploads", response_model=List[dict])
async def list_all_uploads(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncIOMotorClient = Depends(get_db)
):
    """List all uploads (admin only)"""
    jobs = await db.video_jobs.find({}).to_list(length=None)
    
    return [
        {
            "job_id": job["id"],
            "user_id": job.get("user_id"),
            "filename": job["filename"],
            "original_size": job["original_size"],
            "status": job["status"],
            "created_at": job["created_at"],
            "splits_count": len(job.get("splits", []))
        }
        for job in jobs
    ]

@admin_router.delete("/uploads/{job_id}")
async def delete_upload_admin(
    job_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncIOMotorClient = Depends(get_db)
):
    """Delete upload (admin only)"""
    # Delete the job (this will trigger cleanup via existing cleanup endpoint)
    result = await db.video_jobs.delete_one({"id": job_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    return {"message": "Upload deleted successfully"}

@admin_router.get("/settings", response_model=SystemSettings)
async def get_system_settings(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncIOMotorClient = Depends(get_db)
):
    """Get system settings (admin only)"""
    auth_service = get_auth_service(db)
    settings = await auth_service.get_system_settings()
    
    return SystemSettings(
        allow_user_registration=settings.get("allow_user_registration", False),
        max_failed_login_attempts=settings.get("max_failed_login_attempts", 5),
        account_lockout_duration=settings.get("account_lockout_duration", 30)
    )

@admin_router.put("/settings", response_model=SystemSettings)
async def update_system_settings(
    request: SystemSettings,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncIOMotorClient = Depends(get_db)
):
    """Update system settings (admin only)"""
    auth_service = get_auth_service(db)
    
    settings_data = request.dict()
    await auth_service.update_system_settings(settings_data)
    
    return request