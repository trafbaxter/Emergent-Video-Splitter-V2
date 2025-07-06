import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Environment, FileSystemLoader
from typing import List
import secrets
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path

# Email configuration - with defaults to prevent import errors
conf = None

def get_email_config():
    """Get email configuration, creating it if needed"""
    global conf
    if conf is None:
        conf = ConnectionConfig(
            MAIL_USERNAME=os.getenv("SES_SMTP_USER", ""),
            MAIL_PASSWORD=os.getenv("SES_SMTP_PASSWORD", ""),
            MAIL_FROM=os.getenv("FROM_EMAIL", "noreply@example.com"),
            MAIL_PORT=int(os.getenv("SES_SMTP_PORT", 587)),
            MAIL_SERVER=os.getenv("SES_SMTP_SERVER", "smtp.example.com"),
            MAIL_FROM_NAME="Video Splitter Pro",
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
    return conf

class EmailService:
    """Email service for sending authentication emails via AWS SES"""
    
    def __init__(self, db: AsyncIOMotorClient):
        self.fastmail = FastMail(conf)
        self.db = db
        self.tokens_collection = db.email_tokens
        
        # Create email templates directory if it doesn't exist
        self.templates_dir = Path(__file__).parent / "templates"
        self.templates_dir.mkdir(exist_ok=True)
        
        # Create email templates
        self._create_email_templates()
        
        # Initialize Jinja2 environment
        self.template_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir))
        )
        
        # Create TTL index for automatic token expiration (1 hour)
        self._create_indexes()
    
    async def _create_indexes(self):
        """Create database indexes for email tokens"""
        try:
            await self.tokens_collection.create_index("expires_at", expireAfterSeconds=0)
            await self.tokens_collection.create_index("token", unique=True)
        except Exception as e:
            print(f"Index creation error (may already exist): {e}")
    
    def _create_email_templates(self):
        """Create email templates"""
        # Email verification template
        verification_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { padding: 30px; background-color: #f8f9fa; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
        .logo { font-size: 24px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🎬 Video Splitter Pro</div>
            <h1>Verify Your Email Address</h1>
        </div>
        <div class="content">
            <p>Hello {{ user_name }},</p>
            <p>Thank you for signing up for Video Splitter Pro! Please click the button below to verify your email address:</p>
            <p style="text-align: center;">
                <a href="{{ verification_link }}" class="button">Verify Email Address</a>
            </p>
            <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
            <p><a href="{{ verification_link }}">{{ verification_link }}</a></p>
            <p>This link will expire in 1 hour for security reasons.</p>
            <p>If you didn't create an account, please ignore this email.</p>
            <p>Best regards,<br>The Video Splitter Pro Team</p>
        </div>
        <div class="footer">
            <p>&copy; 2024 Video Splitter Pro. All rights reserved.</p>
        </div>
    </div>
</body>
</html>"""
        
        # Password reset template
        password_reset_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { padding: 30px; background-color: #f8f9fa; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
        .logo { font-size: 24px; font-weight: bold; }
        .warning { background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🎬 Video Splitter Pro</div>
            <h1>Reset Your Password</h1>
        </div>
        <div class="content">
            <p>Hello {{ user_name }},</p>
            <p>We received a request to reset your password for your Video Splitter Pro account. Click the button below to create a new password:</p>
            <p style="text-align: center;">
                <a href="{{ reset_link }}" class="button">Reset Password</a>
            </p>
            <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
            <p><a href="{{ reset_link }}">{{ reset_link }}</a></p>
            <div class="warning">
                <strong>Security Notice:</strong> This link will expire in 1 hour for security reasons. If you didn't request a password reset, please ignore this email or contact support if you have concerns.
            </div>
            <p>Best regards,<br>The Video Splitter Pro Team</p>
        </div>
        <div class="footer">
            <p>&copy; 2024 Video Splitter Pro. All rights reserved.</p>
        </div>
    </div>
</body>
</html>"""
        
        # Welcome email template
        welcome_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Video Splitter Pro</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { padding: 30px; background-color: #f8f9fa; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
        .logo { font-size: 24px; font-weight: bold; }
        .feature { background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🎬 Video Splitter Pro</div>
            <h1>Welcome to Video Splitter Pro!</h1>
        </div>
        <div class="content">
            <p>Hello {{ user_name }},</p>
            <p>Welcome to Video Splitter Pro! Your account has been successfully created and verified.</p>
            <div class="feature">
                <h3>🎯 What you can do:</h3>
                <ul>
                    <li>Split videos by time points, intervals, or chapters</li>
                    <li>Preserve subtitles and audio tracks</li>
                    <li>Choose output quality and format</li>
                    <li>Track your upload history</li>
                    <li>Secure account with 2FA</li>
                </ul>
            </div>
            <p style="text-align: center;">
                <a href="{{ login_link }}" class="button">Start Using Video Splitter Pro</a>
            </p>
            <p>If you have any questions, feel free to contact our support team.</p>
            <p>Best regards,<br>The Video Splitter Pro Team</p>
        </div>
        <div class="footer">
            <p>&copy; 2024 Video Splitter Pro. All rights reserved.</p>
        </div>
    </div>
</body>
</html>"""
        
        # Write templates to files
        with open(self.templates_dir / "verification_email.html", "w") as f:
            f.write(verification_template)
        
        with open(self.templates_dir / "password_reset_email.html", "w") as f:
            f.write(password_reset_template)
        
        with open(self.templates_dir / "welcome_email.html", "w") as f:
            f.write(welcome_template)
    
    def generate_token(self, user_id: str, token_type: str) -> str:
        """Generate secure token for email verification or password reset"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        # Store token in MongoDB
        token_doc = {
            "token": token,
            "user_id": user_id,
            "type": token_type,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "used": False
        }
        
        # Insert token (async operation will be handled by the calling function)
        return token, token_doc
    
    async def save_token(self, token_doc: dict):
        """Save token to database"""
        await self.tokens_collection.insert_one(token_doc)
    
    async def send_verification_email(self, email: str, user_name: str, user_id: str):
        """Send email verification email"""
        try:
            token, token_doc = self.generate_token(user_id, "verification")
            await self.save_token(token_doc)
            
            frontend_url = os.getenv("FRONTEND_URL", "https://email.tads-video-splitter.com")
            verification_link = f"{frontend_url}/verify-email?token={token}"
            
            template = self.template_env.get_template("verification_email.html")
            html_content = template.render(
                user_name=user_name,
                verification_link=verification_link
            )
            
            message = MessageSchema(
                subject="Verify Your Email Address - Video Splitter Pro",
                recipients=[email],
                body=html_content,
                subtype="html"
            )
            
            await self.fastmail.send_message(message)
            return {"message": "Verification email sent", "success": True}
            
        except Exception as e:
            print(f"Error sending verification email: {e}")
            return {"message": f"Failed to send verification email: {str(e)}", "success": False}
    
    async def send_password_reset_email(self, email: str, user_name: str, user_id: str):
        """Send password reset email"""
        try:
            token, token_doc = self.generate_token(user_id, "password_reset")
            await self.save_token(token_doc)
            
            frontend_url = os.getenv("FRONTEND_URL", "https://email.tads-video-splitter.com")
            reset_link = f"{frontend_url}/reset-password?token={token}"
            
            template = self.template_env.get_template("password_reset_email.html")
            html_content = template.render(
                user_name=user_name,
                reset_link=reset_link
            )
            
            message = MessageSchema(
                subject="Reset Your Password - Video Splitter Pro",
                recipients=[email],
                body=html_content,
                subtype="html"
            )
            
            await self.fastmail.send_message(message)
            return {"message": "Password reset email sent", "success": True}
            
        except Exception as e:
            print(f"Error sending password reset email: {e}")
            return {"message": f"Failed to send password reset email: {str(e)}", "success": False}
    
    async def send_welcome_email(self, email: str, user_name: str):
        """Send welcome email to new verified users"""
        try:
            frontend_url = os.getenv("FRONTEND_URL", "https://email.tads-video-splitter.com")
            login_link = f"{frontend_url}/login"
            
            template = self.template_env.get_template("welcome_email.html")
            html_content = template.render(
                user_name=user_name,
                login_link=login_link
            )
            
            message = MessageSchema(
                subject="Welcome to Video Splitter Pro! 🎬",
                recipients=[email],
                body=html_content,
                subtype="html"
            )
            
            await self.fastmail.send_message(message)
            return {"message": "Welcome email sent", "success": True}
            
        except Exception as e:
            print(f"Error sending welcome email: {e}")
            return {"message": f"Failed to send welcome email: {str(e)}", "success": False}
    
    async def verify_token(self, token: str, token_type: str) -> dict:
        """Verify and consume token"""
        token_doc = await self.tokens_collection.find_one({
            "token": token,
            "type": token_type,
            "used": False,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not token_doc:
            return {"valid": False, "message": "Invalid or expired token"}
        
        # Mark token as used
        await self.tokens_collection.update_one(
            {"_id": token_doc["_id"]},
            {"$set": {"used": True}}
        )
        
        return {
            "valid": True,
            "user_id": token_doc["user_id"],
            "message": "Token verified successfully"
        }
    
    async def cleanup_expired_tokens(self):
        """Clean up expired tokens (called periodically)"""
        try:
            result = await self.tokens_collection.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            print(f"Cleaned up {result.deleted_count} expired tokens")
        except Exception as e:
            print(f"Error cleaning up expired tokens: {e}")

# Initialize email service
email_service = None

def get_email_service(db: AsyncIOMotorClient) -> EmailService:
    """Get email service instance"""
    global email_service
    if not email_service:
        email_service = EmailService(db)
    return email_service