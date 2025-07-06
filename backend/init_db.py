import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from auth import AuthUtils

async def create_default_admin():
    """Create default admin user if it doesn't exist"""
    try:
        # Connect to MongoDB
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ['DB_NAME']]
        users_collection = db.users
        
        # Check if default admin already exists
        default_username = os.getenv("DEFAULT_ADMIN_USERNAME", "tadmin")
        existing_admin = await users_collection.find_one({"username": default_username})
        
        if existing_admin:
            print(f"Default admin user '{default_username}' already exists")
            return
        
        # Create default admin user
        default_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@videosplitter.com")
        default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "@DefaultUser1234")
        
        # Hash password
        hashed_password = AuthUtils.hash_password(default_password)
        
        # Create admin user document
        admin_user = {
            "id": "default-admin-" + default_username,
            "username": default_username,
            "email": default_email,
            "name": "Default Administrator",
            "role": "admin",
            "password_hash": hashed_password,
            "is_verified": True,  # Admin is pre-verified
            "totp_secret": None,
            "is_2fa_enabled": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None,
            "failed_login_attempts": 0,
            "locked_until": None
        }
        
        # Insert admin user
        await users_collection.insert_one(admin_user)
        
        print(f"✅ Default admin user created successfully!")
        print(f"   Username: {default_username}")
        print(f"   Email: {default_email}")
        print(f"   Password: {default_password}")
        print(f"   Role: admin")
        print(f"   Status: verified")
        print(f"   2FA: disabled (can be enabled after first login)")
        print(f"\n⚠️  SECURITY NOTICE: Please change the default password after first login!")
        
        # Close database connection
        client.close()
        
    except Exception as e:
        print(f"❌ Error creating default admin user: {e}")

async def create_indexes():
    """Create necessary database indexes"""
    try:
        # Connect to MongoDB
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ['DB_NAME']]
        
        # User indexes
        users_collection = db.users
        try:
            await users_collection.create_index("username", unique=True)
            await users_collection.create_index("email", unique=True)
            await users_collection.create_index("id", unique=True)
            print("✅ User indexes created successfully")
        except Exception as e:
            print(f"User indexes (may already exist): {e}")
        
        # Email token indexes
        tokens_collection = db.email_tokens
        try:
            await tokens_collection.create_index("expires_at", expireAfterSeconds=0)
            await tokens_collection.create_index("token", unique=True)
            print("✅ Email token indexes created successfully")
        except Exception as e:
            print(f"Token indexes (may already exist): {e}")
        
        # Video jobs indexes (for user upload history)
        jobs_collection = db.video_jobs
        try:
            await jobs_collection.create_index("user_id")
            await jobs_collection.create_index("id", unique=True)
            print("✅ Video jobs indexes created successfully")
        except Exception as e:
            print(f"Video jobs indexes (may already exist): {e}")
        
        # Settings collection
        settings_collection = db.settings
        try:
            await settings_collection.create_index("type", unique=True)
            print("✅ Settings indexes created successfully")
        except Exception as e:
            print(f"Settings indexes (may already exist): {e}")
        
        # Create default system settings
        existing_settings = await settings_collection.find_one({"type": "system"})
        if not existing_settings:
            default_settings = {
                "type": "system",
                "allow_user_registration": os.getenv("ALLOW_USER_REGISTRATION", "false").lower() == "true",
                "max_failed_login_attempts": 5,
                "account_lockout_duration": 30
            }
            await settings_collection.insert_one(default_settings)
            print("✅ Default system settings created")
        
        # Close database connection
        client.close()
        
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")

async def initialize_database():
    """Initialize database with default data and indexes"""
    print("🚀 Initializing Video Splitter Pro database...")
    
    await create_indexes()
    await create_default_admin()
    
    print("\n✅ Database initialization completed successfully!")
    print("\n🔐 Authentication System Features:")
    print("   - JWT tokens with 3-day refresh")
    print("   - Mandatory email verification")
    print("   - Mandatory 2FA (TOTP)")
    print("   - Password strength requirements")
    print("   - Account lockout protection")
    print("   - Admin user management")
    print("   - Upload history tracking")
    print("   - AWS SES email integration")

if __name__ == "__main__":
    asyncio.run(initialize_database())