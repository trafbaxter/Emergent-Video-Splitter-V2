#!/usr/bin/env python3
"""
Test script to simulate Lambda environment without certain libraries
"""
import sys
import importlib.util

# Temporarily hide the libraries to simulate Lambda environment
original_modules = {}
libraries_to_hide = ['jwt', 'bcrypt', 'pymongo']

for lib in libraries_to_hide:
    if lib in sys.modules:
        original_modules[lib] = sys.modules[lib]
        del sys.modules[lib]

# Mock the import to fail
class MockImportError:
    def find_spec(self, name, path, target=None):
        if name in libraries_to_hide or (name.startswith('pymongo') and 'pymongo' in libraries_to_hide):
            raise ImportError(f"No module named '{name}'")
        return None

# Install the mock importer
sys.meta_path.insert(0, MockImportError())

try:
    # Now try to import our lambda function
    import lambda_function
    
    print("=== Lambda Compatibility Test Results ===")
    print(f"JWT_AVAILABLE: {lambda_function.JWT_AVAILABLE}")
    print(f"BCRYPT_AVAILABLE: {lambda_function.BCRYPT_AVAILABLE}")
    print(f"MONGODB_AVAILABLE: {lambda_function.MONGODB_AVAILABLE}")
    
    # Test that functions handle missing libraries gracefully
    print("\n=== Testing Function Behavior ===")
    
    # Test JWT token generation
    user_data = {'userId': 'test', 'email': 'test@example.com', 'role': 'user'}
    access_token = lambda_function.generate_access_token(user_data)
    print(f"Access token generation result: {access_token}")
    
    # Test MongoDB client
    mongo_client = lambda_function.get_mongo_client()
    print(f"MongoDB client result: {mongo_client}")
    
    print("\n✅ Lambda compatibility test passed!")
    
except Exception as e:
    print(f"❌ Lambda compatibility test failed: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Restore original modules
    sys.meta_path.pop(0)
    for lib, module in original_modules.items():
        sys.modules[lib] = module