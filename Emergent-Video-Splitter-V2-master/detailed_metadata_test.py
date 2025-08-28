#!/usr/bin/env python3
"""
DETAILED METADATA INSPECTION TEST
Inspects the exact structure of the job status response to understand what metadata is present
"""

import requests
import json
import time

# Backend URL from existing configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

def inspect_job_status():
    """Inspect the job status response in detail"""
    job_id = "33749042-9f5e-4fcf-a6ef-4cecbe9c99c5"
    job_status_url = f"{API_BASE}/api/job-status/{job_id}"
    
    print("🔍 DETAILED JOB STATUS INSPECTION")
    print("=" * 60)
    print(f"URL: {job_status_url}")
    print()
    
    try:
        start_time = time.time()
        response = requests.get(job_status_url, timeout=30)
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
                
                # Analyze results array specifically
                if 'results' in data and isinstance(data['results'], list):
                    print(f"RESULTS ARRAY ANALYSIS:")
                    print(f"Number of results: {len(data['results'])}")
                    print()
                    
                    for i, result in enumerate(data['results']):
                        print(f"Result {i+1}:")
                        print(f"  Type: {type(result)}")
                        if isinstance(result, dict):
                            print(f"  Keys: {list(result.keys())}")
                            for key, value in result.items():
                                print(f"    {key}: {value} (type: {type(value).__name__})")
                        else:
                            print(f"  Value: {result}")
                        print()
                        
                else:
                    print("❌ No results array found or invalid format")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"Raw response: {response.text}")
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")

if __name__ == "__main__":
    inspect_job_status()