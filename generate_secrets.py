#!/usr/bin/env python3
"""
Generate secure secrets for production deployment
"""
import secrets
import base64

def generate_jwt_secrets():
    """Generate secure JWT secrets"""
    
    # Generate 256-bit secrets
    jwt_secret = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    refresh_secret = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    
    print("🔐 Generated secure JWT secrets:")
    print("=" * 50)
    print(f"JWT_SECRET={jwt_secret}")
    print(f"JWT_REFRESH_SECRET={refresh_secret}")
    print()
    print("🚨 IMPORTANT: Store these secrets securely!")
    print("1. Add them to your Lambda environment variables")
    print("2. Never commit them to version control")
    print("3. Rotate them regularly")
    
    return jwt_secret, refresh_secret

if __name__ == "__main__":
    generate_jwt_secrets()
