#!/usr/bin/env python3
"""
DETAILED DOWNLOAD API INSPECTION TEST
Inspects the exact structure of the download API response
"""

import requests
import json
import time

# Backend URL from existing configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

def inspect_download_api():
    """Inspect the download API response in detail"""
    job_id = "33749042-9f5e-4fcf-a6ef-4cecbe9c99c5"
    filename = "33749042-9f5e-4fcf-a6ef-4cecbe9c99c5_part_001.mkv"
    download_url = f"{API_BASE}/api/download/{job_id}/{filename}"
    
    print("🔍 DETAILED DOWNLOAD API INSPECTION")
    print("=" * 60)
    print(f"URL: {download_url}")
    print()
    
    try:
        start_time = time.time()
        response = requests.get(download_url, timeout=30)
        response_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response_time:.2f}s")
        print(f"CORS Headers: {response.headers.get('Access-Control-Allow-Origin', 'None')}")
        print()
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("FULL RESPONSE STRUCTURE:")
                print(json.dumps(data, indent=2))
                print()
                
                # Check if download_url is working
                if 'download_url' in data:
                    download_url_value = data['download_url']
                    print(f"DOWNLOAD URL VALIDATION:")
                    print(f"  URL: {download_url_value[:100]}...")
                    print(f"  Length: {len(download_url_value)} characters")
                    print(f"  Starts with https: {download_url_value.startswith('https')}")
                    print(f"  Contains S3: {'s3' in download_url_value.lower()}")
                    print()
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"Raw response: {response.text}")
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")

if __name__ == "__main__":
    inspect_download_api()