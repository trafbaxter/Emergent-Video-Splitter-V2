#!/usr/bin/env python3
"""
Enhanced Authentication System Setup for Video Splitter Pro

This script sets up the enhanced authentication system with:
1. User roles (user/admin)
2. User approval workflow  
3. Soft deletes
4. 2FA setup
5. Password management features
"""

import boto3
import json
import os
from datetime import datetime
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS Configuration
AWS_REGION = 'us-east-1'
USERS_TABLE = 'VideoSplitter-Users'

# Environment variables for initial admin
INITIAL_ADMIN_EMAIL = os.environ.get('INITIAL_ADMIN_EMAIL')
INITIAL_ADMIN_PASSWORD = os.environ.get('INITIAL_ADMIN_PASSWORD')
INITIAL_ADMIN_FIRSTNAME = os.environ.get('INITIAL_ADMIN_FIRSTNAME', 'System')
INITIAL_ADMIN_LASTNAME = os.environ.get('INITIAL_ADMIN_LASTNAME', 'Admin')

def setup_dynamodb_tables():
    """Set up or update DynamoDB tables with enhanced schema"""
    
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    
    try:
        # Get existing Users table
        users_table = dynamodb.Table(USERS_TABLE)
        
        # Check if table exists and get current schema
        try:
            table_info = users_table.table_status
            logger.info(f"✅ Users table exists with status: {table_info}")
            
            # The table exists, we'll update the schema by adding new attributes to existing records
            # DynamoDB is schema-less, so we can add new attributes without modifying the table structure
            
            logger.info("🔄 Table schema will be updated when new records are created")
            return users_table
            
        except Exception as e:
            logger.error(f"❌ Error accessing Users table: {str(e)}")
            raise e
            
    except Exception as e:
        logger.error(f"❌ Error setting up DynamoDB tables: {str(e)}")
        raise e

def hash_password(password):
    """Hash password using bcrypt or fallback"""
    try:
        import bcrypt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except ImportError:
        # Fallback hashing for demo (NOT for production)
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

def create_initial_admin():
    """Create the initial admin user if environment variables are provided"""
    
    if not INITIAL_ADMIN_EMAIL or not INITIAL_ADMIN_PASSWORD:
        logger.warning("⚠️ No initial admin credentials provided via environment variables")
        logger.info("Set INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_PASSWORD to create initial admin")
        return None
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        users_table = dynamodb.Table(USERS_TABLE)
        
        # Check if admin already exists
        from boto3.dynamodb.conditions import Key
        response = users_table.query(
            IndexName='EmailIndex',
            KeyConditionExpression=Key('email').eq(INITIAL_ADMIN_EMAIL)
        )
        
        if response['Items']:
            existing_user = response['Items'][0]
            logger.info(f"✅ Admin user already exists: {INITIAL_ADMIN_EMAIL}")
            
            # Update existing user to admin if not already
            if existing_user.get('user_role') != 'admin':
                users_table.update_item(
                    Key={'user_id': existing_user['user_id']},
                    UpdateExpression='SET user_role = :role, updated_at = :updated_at',
                    ExpressionAttributeValues={
                        ':role': 'admin',
                        ':updated_at': datetime.utcnow().isoformat()
                    }
                )
                logger.info(f"🔄 Updated existing user {INITIAL_ADMIN_EMAIL} to admin role")
            
            return existing_user['user_id']
        
        # Create new admin user
        admin_id = str(uuid.uuid4())
        hashed_password = hash_password(INITIAL_ADMIN_PASSWORD)
        
        admin_user = {
            'user_id': admin_id,
            'email': INITIAL_ADMIN_EMAIL,
            'password': hashed_password,
            'first_name': INITIAL_ADMIN_FIRSTNAME,
            'last_name': INITIAL_ADMIN_LASTNAME,
            'user_role': 'admin',
            'approval_status': 'approved',  # Admin is auto-approved
            'deleted': False,
            'totp_enabled': False,
            'totp_secret': None,
            'force_password_change': False,
            'email_verified': True,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'created_by': 'system',
            'approved_by': 'system',
            'approved_at': datetime.utcnow().isoformat(),
            'last_login': None,
            'failed_login_attempts': 0,
            'locked_until': None,
            'password_reset_token': None,
            'password_reset_expires': None,
            'notes': 'Initial system administrator'
        }
        
        users_table.put_item(Item=admin_user)
        logger.info(f"✅ Created initial admin user: {INITIAL_ADMIN_EMAIL}")
        logger.info(f"   User ID: {admin_id}")
        logger.info(f"   Role: admin")
        logger.info(f"   Status: approved")
        
        return admin_id
        
    except Exception as e:
        logger.error(f"❌ Error creating initial admin: {str(e)}")
        raise e

def update_existing_users():
    """Update existing users with new schema fields"""
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        users_table = dynamodb.Table(USERS_TABLE)
        
        # Scan all existing users
        response = users_table.scan()
        users = response['Items']
        
        logger.info(f"🔄 Found {len(users)} existing users to update")
        
        for user in users:
            user_id = user['user_id']
            updates_needed = []
            update_expression_parts = []
            expression_values = {}
            
            # Add missing fields with default values
            new_fields = {
                'user_role': 'user',  # Default role for existing users
                'approval_status': 'approved',  # Existing users are auto-approved
                'deleted': False,
                'totp_enabled': False,
                'totp_secret': None,
                'force_password_change': False,
                'failed_login_attempts': 0,
                'locked_until': None,
                'password_reset_token': None,
                'password_reset_expires': None,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            for field, default_value in new_fields.items():
                if field not in user:
                    updates_needed.append(field)
                    update_expression_parts.append(f"{field} = :{field}")
                    expression_values[f":{field}"] = default_value
            
            if updates_needed:
                update_expression = "SET " + ", ".join(update_expression_parts)
                
                users_table.update_item(
                    Key={'user_id': user_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_values
                )
                
                logger.info(f"✅ Updated user {user.get('email', user_id)} with fields: {updates_needed}")
            else:
                logger.info(f"✅ User {user.get('email', user_id)} already has all required fields")
        
        logger.info(f"✅ Completed updating {len(users)} existing users")
        
    except Exception as e:
        logger.error(f"❌ Error updating existing users: {str(e)}")
        raise e

def setup_ses_configuration():
    """Set up AWS SES for email notifications"""
    
    try:
        ses_client = boto3.client('ses', region_name=AWS_REGION)
        
        # Get verified email addresses
        response = ses_client.list_verified_email_addresses()
        verified_emails = response['VerifiedEmailAddresses']
        
        logger.info(f"📧 SES Configuration:")
        logger.info(f"   Region: {AWS_REGION}")
        logger.info(f"   Verified emails: {len(verified_emails)}")
        
        if verified_emails:
            for email in verified_emails:
                logger.info(f"   ✅ {email}")
        else:
            logger.warning("   ⚠️ No verified email addresses found")
            logger.info("   Please verify email addresses in AWS SES console for email notifications")
        
        return len(verified_emails) > 0
        
    except Exception as e:
        logger.warning(f"⚠️ Could not check SES configuration: {str(e)}")
        return False

def main():
    """Main setup function"""
    
    logger.info("🚀 Setting up Enhanced Authentication System for Video Splitter Pro")
    logger.info("=" * 70)
    
    try:
        # Step 1: Setup DynamoDB tables
        logger.info("📊 Step 1: Setting up DynamoDB tables...")
        users_table = setup_dynamodb_tables()
        logger.info("✅ DynamoDB setup complete")
        
        # Step 2: Update existing users with new schema
        logger.info("\n🔄 Step 2: Updating existing users...")
        update_existing_users()
        logger.info("✅ User schema updates complete")
        
        # Step 3: Create initial admin user
        logger.info("\n👤 Step 3: Creating initial admin user...")
        admin_id = create_initial_admin()
        if admin_id:
            logger.info("✅ Initial admin setup complete")
        else:
            logger.info("⚠️ Initial admin not created (missing environment variables)")
        
        # Step 4: Check SES configuration
        logger.info("\n📧 Step 4: Checking SES configuration...")
        ses_ready = setup_ses_configuration()
        if ses_ready:
            logger.info("✅ SES configuration looks good")
        else:
            logger.info("⚠️ SES needs additional setup for email notifications")
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("🎉 Enhanced Authentication System Setup Complete!")
        logger.info("\n📋 Summary:")
        logger.info("✅ DynamoDB schema updated with new authentication fields")
        logger.info("✅ Existing users migrated to new schema")
        if admin_id:
            logger.info(f"✅ Initial admin user created: {INITIAL_ADMIN_EMAIL}")
        logger.info("✅ System ready for enhanced authentication features")
        
        logger.info("\n🔧 Next Steps:")
        logger.info("1. Deploy updated Lambda functions with new authentication logic")
        logger.info("2. Update frontend components for new user management features")
        logger.info("3. Test user approval workflow")
        logger.info("4. Configure 2FA settings")
        logger.info("5. Set up email templates for notifications")
        
        if not ses_ready:
            logger.info("\n⚠️ Don't forget to verify email addresses in AWS SES console!")
        
    except Exception as e:
        logger.error(f"\n❌ Setup failed: {str(e)}")
        raise e

if __name__ == "__main__":
    main()