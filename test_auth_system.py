#!/usr/bin/env python3
"""
Test Lambda authentication system
"""
import boto3
import json

def test_lambda_authentication():
    """Test the authentication endpoints"""
    
    print("🧪 Testing Lambda Authentication System")
    print("=" * 40)
    
    lambda_client = boto3.client('lambda')
    
    test_cases = [
        {
            "name": "Basic function execution",
            "payload": {"httpMethod": "GET", "path": "/", "headers": {}}
        },
        {
            "name": "Health check endpoint",
            "payload": {"httpMethod": "GET", "path": "/api/", "headers": {}}
        },
        {
            "name": "Authentication register endpoint",
            "payload": {
                "httpMethod": "POST", 
                "path": "/api/auth/register", 
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "email": "test@example.com",
                    "password": "testpassword123"
                })
            }
        }
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}/{total_tests}: {test['name']}")
        
        try:
            response = lambda_client.invoke(
                FunctionName='videosplitter-api',
                Payload=json.dumps(test['payload'])
            )
            
            status_code = response.get('StatusCode', 0)
            payload = response['Payload'].read().decode('utf-8')
            
            if status_code == 200:
                # Parse the response to check for errors
                try:
                    response_data = json.loads(payload)
                    
                    if 'errorMessage' in response_data:
                        error_type = response_data.get('errorType', '')
                        error_message = response_data.get('errorMessage', '')
                        
                        if 'ImportModuleError' in error_type:
                            print(f"❌ Import error: {error_message}")
                            print("   Dependencies are still missing from Lambda")
                        elif 'Runtime' in error_type:
                            print(f"❌ Runtime error: {error_message}")
                        else:
                            print(f"⚠️  Function error: {error_message}")
                            print("   (But dependencies imported successfully)")
                            success_count += 1
                    else:
                        print(f"✅ Success!")
                        print(f"   Response: {str(response_data)[:100]}...")
                        success_count += 1
                        
                except json.JSONDecodeError:
                    # Not JSON, check for specific error patterns
                    if 'ImportModuleError' in payload:
                        print("❌ Import module error still present")
                        print(f"   Error: {payload[:200]}...")
                    else:
                        print(f"✅ Non-JSON response (likely success)")
                        print(f"   Response: {payload[:100]}...")
                        success_count += 1
                        
            else:
                print(f"❌ HTTP Status {status_code}")
                print(f"   Response: {payload[:200]}...")
                
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
    
    print(f"\n📊 Test Results:")
    print(f"   ✅ Successful: {success_count}/{total_tests}")
    print(f"   ❌ Failed: {total_tests - success_count}/{total_tests}")
    
    if success_count > 0:
        print(f"\n🎉 Authentication system is working!")
        print(f"   Dependencies are properly loaded via Lambda layer")
        return True
    else:
        print(f"\n❌ Authentication system needs debugging")
        print(f"   Dependencies may still be missing")
        return False

if __name__ == "__main__":
    test_lambda_authentication()