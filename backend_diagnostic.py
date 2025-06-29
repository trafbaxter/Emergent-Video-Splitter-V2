#!/usr/bin/env python3
import os
import requests
import json
import sys
import socket

def check_local_backend():
    """Check if the backend is running locally and on which port"""
    print("\n=== Checking local backend service ===")
    
    # Try port 8000 (from supervisor config)
    try:
        response = requests.get("http://localhost:8000/api/")
        if response.status_code == 200:
            print(f"✅ Backend is running on port 8000: {response.text}")
            return 8000
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not accessible on port 8000")
    
    # Try port 8001 (mentioned in requirements)
    try:
        response = requests.get("http://localhost:8001/api/")
        if response.status_code == 200:
            print(f"✅ Backend is running on port 8001: {response.text}")
            return 8001
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not accessible on port 8001")
    
    # Try to find the port by checking common ports
    for port in [3000, 5000, 8080, 8888, 9000]:
        try:
            response = requests.get(f"http://localhost:{port}/api/")
            if response.status_code == 200:
                print(f"✅ Backend found on port {port}: {response.text}")
                return port
        except requests.exceptions.ConnectionError:
            pass
    
    print("❌ Could not find backend service on any common port")
    return None

def check_public_url():
    """Check if the public URL is accessible"""
    print("\n=== Checking public URL configuration ===")
    
    # Get the backend URL from the frontend .env file
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.strip().split('=')[1].strip('"\'')
                break
    
    # Ensure the URL has no trailing slash
    BACKEND_URL = BACKEND_URL.rstrip('/')
    API_URL = f"{BACKEND_URL}/api"
    
    print(f"Public API URL: {API_URL}")
    
    try:
        # Try to resolve the hostname
        hostname = BACKEND_URL.replace("https://", "").replace("http://", "").split("/")[0]
        print(f"Resolving hostname: {hostname}")
        ip_address = socket.gethostbyname(hostname)
        print(f"✅ Hostname resolves to IP: {ip_address}")
    except socket.gaierror:
        print(f"❌ Could not resolve hostname: {hostname}")
    
    try:
        response = requests.get(f"{API_URL}/", timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Public URL is accessible")
            return True
        else:
            print(f"❌ Public URL returned non-200 status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error accessing public URL: {e}")
        return False

def check_cors_configuration():
    """Check if CORS is properly configured"""
    print("\n=== Checking CORS configuration ===")
    
    # Check the server.py file for CORS configuration
    try:
        with open('/app/backend/server.py', 'r') as f:
            server_code = f.read()
            
            if 'CORSMiddleware' in server_code and 'allow_origins' in server_code:
                print("✅ CORS middleware is configured in server.py")
                
                # Check if allow_origins includes "*" or the frontend URL
                if '"*"' in server_code or "'*'" in server_code:
                    print("✅ CORS is configured to allow all origins (*)")
                else:
                    with open('/app/frontend/.env', 'r') as f:
                        for line in f:
                            if line.startswith('REACT_APP_BACKEND_URL='):
                                BACKEND_URL = line.strip().split('=')[1].strip('"\'')
                                if BACKEND_URL in server_code:
                                    print(f"✅ CORS is configured to allow the frontend URL: {BACKEND_URL}")
                                else:
                                    print(f"❌ CORS may not be configured to allow the frontend URL: {BACKEND_URL}")
            else:
                print("❌ CORS middleware is not properly configured in server.py")
    except Exception as e:
        print(f"Error checking CORS configuration: {e}")

def check_port_forwarding():
    """Check if port forwarding is properly configured"""
    print("\n=== Checking port forwarding configuration ===")
    
    # Check supervisor configuration
    try:
        with open('/etc/supervisor/conf.d/supervisord.conf', 'r') as f:
            supervisor_config = f.read()
            
            if 'backend' in supervisor_config:
                import re
                port_match = re.search(r'--port\s+(\d+)', supervisor_config)
                if port_match:
                    backend_port = port_match.group(1)
                    print(f"✅ Backend is configured to run on port {backend_port} in supervisor")
                else:
                    print("❌ Could not determine backend port from supervisor config")
    except Exception as e:
        print(f"Error checking supervisor configuration: {e}")
    
    # Check if nginx is running and configured
    try:
        result = os.system("which nginx > /dev/null 2>&1")
        if result == 0:
            print("✅ Nginx is installed")
            
            # Check nginx configuration
            nginx_conf_paths = [
                "/etc/nginx/sites-enabled/default",
                "/etc/nginx/conf.d/default.conf",
                "/etc/nginx/nginx.conf"
            ]
            
            for path in nginx_conf_paths:
                if os.path.exists(path):
                    print(f"Found nginx config at: {path}")
                    with open(path, 'r') as f:
                        nginx_config = f.read()
                        if 'proxy_pass' in nginx_config and ('8000' in nginx_config or '8001' in nginx_config):
                            print("✅ Nginx is configured with proxy_pass for the backend")
                        else:
                            print("❌ Nginx may not be properly configured for the backend")
        else:
            print("ℹ️ Nginx is not installed, may be using another proxy")
    except Exception as e:
        print(f"Error checking nginx configuration: {e}")

def main():
    print("=== Backend Connectivity Diagnostic Tool ===")
    
    # Check if backend is running locally
    local_port = check_local_backend()
    
    # Check public URL
    public_accessible = check_public_url()
    
    # Check CORS configuration
    check_cors_configuration()
    
    # Check port forwarding
    check_port_forwarding()
    
    # Summary
    print("\n=== Diagnostic Summary ===")
    if local_port:
        print(f"✅ Backend is running locally on port {local_port}")
    else:
        print("❌ Backend is not accessible locally")
    
    if public_accessible:
        print("✅ Backend is accessible via public URL")
    else:
        print("❌ Backend is not accessible via public URL")
    
    # Recommendations
    print("\n=== Recommendations ===")
    if local_port and not public_accessible:
        print("1. The backend is running locally but not accessible via the public URL.")
        print("   This suggests an issue with the proxy configuration or port forwarding.")
        print(f"2. The backend is running on port {local_port}, but the frontend may be trying to access it on a different port.")
        print("3. Check that the Kubernetes ingress or proxy is correctly forwarding requests to the backend.")
        print("4. Verify that the CORS configuration allows requests from the frontend origin.")
    elif not local_port:
        print("1. The backend service is not running or not accessible locally.")
        print("2. Check the backend logs for errors.")
        print("3. Restart the backend service: sudo supervisorctl restart backend")
    
    if local_port == 8000 and not public_accessible:
        print("\nPOTENTIAL SOLUTION:")
        print("The backend is running on port 8000, but the review request mentioned port 8001.")
        print("This mismatch could be causing the connectivity issue.")
        print("Options:")
        print("1. Update the supervisor configuration to use port 8001 instead of 8000")
        print("2. Update the frontend configuration to use port 8000 instead of 8001")
        print("3. Configure the proxy to forward requests from the public URL to port 8000")

if __name__ == "__main__":
    main()