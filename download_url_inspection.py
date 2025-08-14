#!/usr/bin/env python3
"""
DOWNLOAD URL INSPECTION
Inspect the actual download URLs returned by the API to understand the format
"""

import requests
import json

# Backend URL from environment configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'
KNOWN_JOB_ID = "ddff83c7-d5fe-424c-adf0-6e97ee5fd4ae"

def inspect_download_urls():
    print("🔍 INSPECTING DOWNLOAD URLs")
    print("=" * 60)
    
    # First get job status to get filenames
    print("1. Getting job status...")
    response = requests.get(f"{API_BASE}/api/job-status/{KNOWN_JOB_ID}")
    
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        
        if results:
            filename = results[0].get('filename')
            print(f"   Found filename: {filename}")
            
            # Test download endpoint
            print(f"\n2. Testing download endpoint...")
            download_url = f"{API_BASE}/api/download/{KNOWN_JOB_ID}/{filename}"
            print(f"   Request URL: {download_url}")
            
            download_response = requests.get(download_url)
            print(f"   Response Status: {download_response.status_code}")
            
            if download_response.status_code == 200:
                download_data = download_response.json()
                
                print(f"\n3. Response Analysis:")
                print(f"   Response Keys: {list(download_data.keys())}")
                
                download_url_field = download_data.get('download_url', '')
                filename_field = download_data.get('filename', '')
                expires_in = download_data.get('expires_in', '')
                
                print(f"\n4. Field Analysis:")
                print(f"   filename: {filename_field}")
                print(f"   expires_in: {expires_in}")
                print(f"   download_url length: {len(download_url_field)} characters")
                
                print(f"\n5. Download URL Analysis:")
                print(f"   Full URL: {download_url_field}")
                
                # Check URL components
                url_checks = []
                if 'amazonaws.com' in download_url_field:
                    url_checks.append("✅ Contains amazonaws.com")
                else:
                    url_checks.append("❌ Missing amazonaws.com")
                    
                if 'X-Amz-Signature' in download_url_field:
                    url_checks.append("✅ Contains X-Amz-Signature")
                else:
                    url_checks.append("❌ Missing X-Amz-Signature")
                    
                if 'X-Amz-Expires' in download_url_field:
                    url_checks.append("✅ Contains X-Amz-Expires")
                else:
                    url_checks.append("❌ Missing X-Amz-Expires")
                    
                if download_url_field.startswith('http'):
                    url_checks.append("✅ Starts with http")
                else:
                    url_checks.append("❌ Doesn't start with http")
                
                print(f"\n6. URL Validation:")
                for check in url_checks:
                    print(f"   {check}")
                
                # Test if URL is accessible
                print(f"\n7. URL Accessibility Test:")
                try:
                    test_response = requests.head(download_url_field, timeout=5)
                    print(f"   HEAD request status: {test_response.status_code}")
                    print(f"   Content-Type: {test_response.headers.get('Content-Type', 'Not specified')}")
                    print(f"   Content-Length: {test_response.headers.get('Content-Length', 'Not specified')}")
                except Exception as e:
                    print(f"   HEAD request failed: {str(e)}")
                
            else:
                print(f"   Download request failed: {download_response.text}")
        else:
            print("   No results found in job status")
    else:
        print(f"   Job status request failed: {response.status_code}")

if __name__ == "__main__":
    inspect_download_urls()