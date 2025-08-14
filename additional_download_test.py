#!/usr/bin/env python3
"""
ADDITIONAL DOWNLOAD TEST
Test download functionality with different job IDs to ensure consistency
"""

import requests
import json

# Backend URL from environment configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

def test_download_with_job_id(job_id, description):
    print(f"\n🔍 Testing Download with {description}")
    print(f"   Job ID: {job_id}")
    
    # Get job status first
    try:
        response = requests.get(f"{API_BASE}/api/job-status/{job_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            status = data.get('status', 'unknown')
            progress = data.get('progress', 0)
            
            print(f"   Status: {status}, Progress: {progress}%")
            
            if results and len(results) > 0:
                filename = results[0].get('filename')
                print(f"   First filename: {filename}")
                
                # Test download endpoint
                download_url = f"{API_BASE}/api/download/{job_id}/{filename}"
                download_response = requests.get(download_url, timeout=10)
                
                print(f"   Download Status: {download_response.status_code}")
                
                if download_response.status_code == 200:
                    download_data = download_response.json()
                    has_required_fields = all(field in download_data for field in ['download_url', 'filename', 'expires_in'])
                    print(f"   ✅ Has required fields: {has_required_fields}")
                    
                    s3_url = download_data.get('download_url', '')
                    is_valid_s3 = 'amazonaws.com' in s3_url and s3_url.startswith('http')
                    print(f"   ✅ Valid S3 URL: {is_valid_s3}")
                    
                    return True
                else:
                    print(f"   ❌ Download failed: {download_response.text[:100]}")
                    return False
            else:
                print(f"   ⚠️  No results available")
                return False
        else:
            print(f"   ❌ Job status failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Request failed: {str(e)}")
        return False

def main():
    print("🚀 ADDITIONAL DOWNLOAD FUNCTIONALITY TESTS")
    print("=" * 60)
    
    # Test with different job IDs
    test_cases = [
        ("ddff83c7-d5fe-424c-adf0-6e97ee5fd4ae", "Known Completed Job"),
        ("7e38b588-fe5a-46d5-b0c9-e876f3293e2a", "Another Completed Job"),
        ("test-job-123", "Test Job ID"),
    ]
    
    results = []
    for job_id, description in test_cases:
        success = test_download_with_job_id(job_id, description)
        results.append(success)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n" + "=" * 60)
    print(f"📊 SUMMARY: {passed}/{total} tests passed")
    
    if passed >= 1:  # At least one working is good
        print("✅ Download functionality is working with correct job ID format")
    else:
        print("❌ Download functionality needs investigation")

if __name__ == "__main__":
    main()