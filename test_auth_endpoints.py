#!/usr/bin/env python3
"""
Test authentication endpoints with missing libraries
"""
import sys
import json

# Hide libraries to simulate Lambda environment
libraries_to_hide = ['jwt', 'bcrypt', 'pymongo']
for lib in libraries_to_hide:
    if lib in sys.modules:
        del sys.modules[lib]

class MockImportError:
    def find_spec(self, name, path, target=None):
        if name in libraries_to_hide or (name.startswith('pymongo') and 'pymongo' in libraries_to_hide):
            raise ImportError(f"No module named '{name}'")
        return None

sys.meta_path.insert(0, MockImportError())

try:
    import lambda_function
    
    print("=== Testing Authentication Endpoints ===")
    
    # Mock event for user registration
    registration_event = {
        'body': json.dumps({
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'firstName': 'Test',
            'lastName': 'User'
        })
    }
    
    # Mock context
    class MockContext:
        aws_request_id = 'test-request-id'
    
    context = MockContext()
    
    # Test user registration
    print("\n--- Testing User Registration ---")
    result = lambda_function.handle_user_registration(registration_event, context)
    print(f"Status Code: {result['statusCode']}")
    body = json.loads(result['body'])
    print(f"Response: {body}")
    
    # Test user login
    print("\n--- Testing User Login ---")
    login_event = {
        'body': json.dumps({
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        })
    }
    
    result = lambda_function.handle_user_login(login_event, context)
    print(f"Status Code: {result['statusCode']}")
    body = json.loads(result['body'])
    print(f"Response: {body}")
    
    print("\n✅ Authentication endpoint test completed!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()

finally:
    sys.meta_path.pop(0)