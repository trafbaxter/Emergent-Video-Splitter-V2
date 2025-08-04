#!/usr/bin/env python3
"""
Update main Lambda function to support user authentication
"""
import json
import os

def update_lambda_function():
    """Update the main lambda function to include authentication support"""
    
    print("🔄 Updating main Lambda function for authentication integration...")
    
    # Read current lambda function
    with open('/app/lambda_function.py', 'r') as f:
        current_content = f.read()
    
    # Add authentication imports and functions
    auth_imports = """
import jwt
from datetime import datetime
"""
    
    # Add JWT validation function
    jwt_validation_function = '''
def validate_jwt_from_context(event):
    """Extract and validate user information from API Gateway context"""
    try:
        # Get user context from API Gateway authorizer
        request_context = event.get('requestContext', {})
        authorizer_context = request_context.get('authorizer', {})
        
        user_id = authorizer_context.get('userId')
        user_email = authorizer_context.get('email')
        user_role = authorizer_context.get('role', 'user')
        
        if not user_id:
            logger.error("No user ID found in request context")
            return None
            
        return {
            'userId': user_id,
            'email': user_email,
            'role': user_role
        }
        
    except Exception as e:
        logger.error(f"Error validating JWT from context: {str(e)}")
        return None

def require_authentication(func):
    """Decorator to require authentication for endpoints"""
    def wrapper(event, context):
        user_context = validate_jwt_from_context(event)
        if not user_context:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Authentication required',
                    'message': 'Please log in to access this resource'
                })
            }
        
        # Add user context to event for use in the function
        event['userContext'] = user_context
        return func(event, context)
    
    return wrapper
'''
    
    # Add user-specific file operations
    user_file_functions = '''
def get_user_files_path(user_id):
    """Get S3 path prefix for user-specific files"""
    return f"user-files/{user_id}/"

def get_user_upload_history(user_id):
    """Get upload history for specific user"""
    try:
        from pymongo import MongoClient
        
        # Connect to MongoDB
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        client = MongoClient(mongo_url)
        db = client['videosplitter']
        users_collection = db.users
        
        # Find user and return upload history
        user = users_collection.find_one({'userId': user_id})
        if user:
            return user.get('uploadHistory', [])
        
        return []
        
    except Exception as e:
        logger.error(f"Error getting user upload history: {str(e)}")
        return []

def add_to_user_upload_history(user_id, upload_data):
    """Add upload record to user's history"""
    try:
        from pymongo import MongoClient
        from datetime import datetime
        
        # Connect to MongoDB
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        client = MongoClient(mongo_url)
        db = client['videosplitter']
        users_collection = db.users
        
        # Add to upload history
        upload_record = {
            'uploadId': upload_data.get('uploadId'),
            'fileName': upload_data.get('fileName'),
            'fileSize': upload_data.get('fileSize', 0),
            'uploadedAt': datetime.utcnow(),
            'status': 'uploaded',
            'processingStatus': 'pending'
        }
        
        users_collection.update_one(
            {'userId': user_id},
            {'$push': {'uploadHistory': upload_record}}
        )
        
        logger.info(f"Added upload record to user {user_id} history")
        
    except Exception as e:
        logger.error(f"Error adding to user upload history: {str(e)}")
'''
    
    # Update the file to add imports
    if "import jwt" not in current_content:
        # Add imports after existing imports
        import_section_end = current_content.find("# Initialize")
        if import_section_end == -1:
            import_section_end = current_content.find("logger = logging.getLogger()")
        
        if import_section_end != -1:
            current_content = (
                current_content[:import_section_end] + 
                auth_imports + "\n" +
                current_content[import_section_end:]
            )
    
    # Add authentication functions before the main handler
    handler_index = current_content.find("def lambda_handler(")
    if handler_index != -1 and "validate_jwt_from_context" not in current_content:
        current_content = (
            current_content[:handler_index] + 
            jwt_validation_function + "\n" +
            user_file_functions + "\n" +
            current_content[handler_index:]
        )
    
    # Update specific endpoints to be user-aware
    # Update the video info endpoint
    if "def handle_video_info" in current_content:
        # Make video info user-aware
        current_content = current_content.replace(
            "def handle_video_info(event: Dict[str, Any], context) -> Dict[str, Any]:",
            "def handle_video_info(event: Dict[str, Any], context) -> Dict[str, Any]:\n    \"\"\"Handle video info request with user authentication\"\"\"\n    user_context = validate_jwt_from_context(event)\n    if not user_context:\n        return {\n            'statusCode': 401,\n            'headers': get_cors_headers(),\n            'body': json.dumps({'error': 'Authentication required'})\n        }"
        )
    
    # Write updated content back to file
    with open('/app/lambda_function.py', 'w') as f:
        f.write(current_content)
    
    print("✅ Main Lambda function updated with authentication support!")
    
    # Now deploy the updated function
    print("🚀 Deploying updated main Lambda function...")
    os.system("cd /app && python3 update_lambda.py")

if __name__ == "__main__":
    update_lambda_function()