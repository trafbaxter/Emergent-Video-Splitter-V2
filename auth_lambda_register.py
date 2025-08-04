#!/usr/bin/env python3
"""
User Registration Lambda Function
Handles user registration with email verification
"""
import json
import bcrypt
import os
import uuid
import re
from datetime import datetime, timedelta
from pymongo import MongoClient
import boto3
from botocore.exceptions import ClientError

# Environment variables (will be set in Lambda)
MONGODB_URI = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = 'videosplitter'  # Use existing database
AWS_ACCESS_KEY = 'REDACTED_AWS_KEY'
AWS_SECRET_KEY = 'kSLXhxXDBZjgxZF9nHZHG8cZKrHM6KrNKv4gCXBE'
FRONTEND_URL = 'https://develop.tads-video-splitter.com'

def lambda_handler(event, context):
    """Handle user registration requests"""
    try:
        print(f"Registration request received: {event}")
        
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': ''
            }
        
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract registration data
        email = body.get('email', '').lower().strip()
        password = body.get('password', '')
        first_name = body.get('firstName', '').strip()
        last_name = body.get('lastName', '').strip()
        
        print(f"Registration attempt for email: {email}")
        
        # Validate input data
        validation_errors = validate_registration_data(email, password, first_name, last_name)
        if validation_errors:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'success': False,
                    'message': 'Validation failed',
                    'errors': validation_errors
                })
            }
        
        # Connect to MongoDB
        client = MongoClient(MONGODB_URI)
        db = client[DB_NAME]
        users_collection = db.users
        
        # Check if user already exists
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            return {
                'statusCode': 409,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'success': False,
                    'message': 'User with this email already exists'
                })
            }
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Generate verification token
        verification_token = str(uuid.uuid4())
        
        # Create user document
        user_data = {
            'userId': str(uuid.uuid4()),
            'email': email,
            'passwordHash': password_hash,
            'firstName': first_name,
            'lastName': last_name,
            'role': 'user',
            'isEmailVerified': False,
            'emailVerificationToken': verification_token,
            'profileImage': None,
            'uploadHistory': [],
            'accountSettings': {
                'emailNotifications': True,
                'securityAlerts': True
            },
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow(),
            'lastLoginAt': None,
            'loginAttempts': 0,
            'accountLocked': False,
            'lockedUntil': None
        }
        
        # Insert user into database
        result = users_collection.insert_one(user_data)
        print(f"User created with ID: {user_data['userId']}")
        
        # Send verification email
        email_success = send_verification_email(email, first_name, verification_token)
        
        if not email_success:
            print("Warning: Verification email failed to send")
        
        return {
            'statusCode': 201,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'success': True,
                'message': 'User registered successfully. Please check your email for verification.',
                'userId': user_data['userId'],
                'emailSent': email_success
            })
        }
        
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'success': False,
                'message': 'Internal server error during registration',
                'error': str(e)
            })
        }

def validate_registration_data(email, password, first_name, last_name):
    """Validate registration input data"""
    errors = []
    
    # Email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email or not re.match(email_pattern, email):
        errors.append('Valid email address is required')
    
    # Password validation (strong password policy)
    if not password:
        errors.append('Password is required')
    elif len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    elif not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter')
    elif not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter')
    elif not re.search(r'\d', password):
        errors.append('Password must contain at least one number')
    elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('Password must contain at least one special character')
    
    # Name validation
    if not first_name or len(first_name.strip()) < 2:
        errors.append('First name must be at least 2 characters long')
    
    if not last_name or len(last_name.strip()) < 2:
        errors.append('Last name must be at least 2 characters long')
    
    return errors

def send_verification_email(email, first_name, verification_token):
    """Send email verification using AWS SES"""
    try:
        ses_client = boto3.client(
            'ses',
            region_name='us-east-1',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY
        )
        
        verification_url = f"{FRONTEND_URL}/verify-email?token={verification_token}"
        
        subject = "Verify Your Tad's Video Splitter Account"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ padding: 30px; background-color: #f9fafb; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Tad's Video Splitter!</h1>
                </div>
                <div class="content">
                    <h2>Hello {first_name},</h2>
                    <p>Thank you for creating your account with Tad's Video Splitter. To complete your registration and start splitting videos, please verify your email address by clicking the button below:</p>
                    
                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </div>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #e5e7eb; padding: 10px; border-radius: 4px;">{verification_url}</p>
                    
                    <p><strong>Security Notice:</strong> This verification link will expire in 24 hours for your security. If you didn't create this account, please ignore this email.</p>
                    
                    <p>Once verified, you'll be able to:</p>
                    <ul>
                        <li>Upload and split video files</li>
                        <li>Access your upload history</li>
                        <li>Manage your account settings</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>If you have any questions, please contact us.</p>
                    <p>&copy; {datetime.now().year} Tad's Video Splitter. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
Welcome to Tad's Video Splitter!

Hello {first_name},

Thank you for creating your account. Please verify your email address by visiting:

{verification_url}

This link will expire in 24 hours for security purposes.

If you didn't create this account, please ignore this email.

Best regards,
Tad's Video Splitter Team
        """
        
        # Send email
        response = ses_client.send_email(
            Source="Tad's Video Splitter <noreply@tads-video-splitter.com>",
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Html': {'Data': html_body, 'Charset': 'UTF-8'},
                    'Text': {'Data': text_body, 'Charset': 'UTF-8'}
                }
            }
        )
        
        print(f"Verification email sent successfully: {response['MessageId']}")
        return True
        
    except ClientError as e:
        print(f"SES error sending verification email: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"Error sending verification email: {str(e)}")
        return False

def get_cors_headers():
    """Get CORS headers for API Gateway"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE',
        'Content-Type': 'application/json'
    }

if __name__ == "__main__":
    # Test locally
    test_event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'firstName': 'Test',
            'lastName': 'User'
        })
    }
    
    result = lambda_handler(test_event, None)
    print(f"Test result: {result}")