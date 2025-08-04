#!/usr/bin/env python3
"""
Security audit script to check for hardcoded secrets
"""
import os
import re
from pathlib import Path

def check_for_hardcoded_secrets():
    """Scan files for potential hardcoded secrets"""
    
    # Patterns to look for
    patterns = {
        'AWS Access Key': r'AKIA[0-9A-Z]{16}',
        'AWS Secret Key': r'["\'][0-9a-zA-Z/+]{40}["\']',  # Only match quoted strings
        'MongoDB URI with credentials': r'mongodb://[^:]+:[^@]+@[^/]+',  # More specific pattern
        'JWT Secret (long strings)': r'["\']([a-zA-Z0-9-_]{50,})["\']',
        'Email addresses in code': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'Hardcoded passwords': r'password\s*[:=]\s*["\'][^"\']{8,}["\']'
    }
    
    # File extensions to check
    extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.json', '.yaml', '.yml', '.env']
    
    # Directories to skip
    skip_dirs = {'node_modules', '.git', '__pycache__', 'lambda_deps', 'python_deps', 'final_lambda', 'build', 'dist', 'amplify'}
    
    # Files to skip (contain only package metadata, not secrets)
    skip_files = {'package-lock.json', 'yarn.lock', 'cli.json'}
    
    findings = []
    
    print("🔍 Scanning for hardcoded secrets...")
    print("=" * 60)
    
    for root, dirs, files in os.walk('/app'):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions) and file not in skip_files:
                file_path = Path(root) / file
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        for pattern_name, pattern in patterns.items():
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            
                            if matches:
                                for match in matches:
                                    # Skip certain safe patterns
                                    if isinstance(match, tuple):
                                        match = match[0] if match else ''
                                    
                                    # Skip example/placeholder values and false positives
                                    skip_patterns = [
                                        'your-', 'example', 'placeholder', 'change-this',
                                        'test@example.com', 'user@example.com',
                                        'localhost', '127.0.0.1', 'reactInternalMemoized',
                                        'dangerouslyConnectToHttpEndpointForTesti',
                                        'usefieldnameforprimarykeyconnectionfield',
                                        'respectprimarykeyattributesonconnectionf',
                                        'generatemodelsforlazyloadandcustomselect',
                                        'mongodb://[^:]+:[^@', 'r\'mongodb://', 'mongodb URI pattern'
                                    ]
                                    
                                    if any(skip in str(match).lower() for skip in skip_patterns):
                                        continue
                                    
                                    findings.append({
                                        'file': str(file_path),
                                        'type': pattern_name,
                                        'match': str(match)[:50] + '...' if len(str(match)) > 50 else str(match),
                                        'line_content': ''
                                    })
                
                except Exception as e:
                    print(f"⚠️  Error reading {file_path}: {e}")
    
    # Report findings
    if findings:
        print("❌ POTENTIAL SECURITY ISSUES FOUND:")
        print("-" * 60)
        
        for finding in findings:
            print(f"🚨 {finding['type']}")
            print(f"   File: {finding['file']}")
            print(f"   Match: {finding['match']}")
            print()
    else:
        print("✅ No obvious hardcoded secrets found!")
    
    # Check environment variable usage
    print("\n🔐 Environment Variable Usage:")
    print("-" * 40)
    
    env_vars = [
        'JWT_SECRET', 'JWT_REFRESH_SECRET', 'MONGO_URL', 
        'AWS_REGION', 'FRONTEND_URL', 'SES_SENDER_EMAIL'
    ]
    
    for var in env_vars:
        if var in os.environ:
            value = os.environ[var]
            masked = value[:5] + '*' * (len(value) - 10) + value[-5:] if len(value) > 10 else '*' * len(value)
            print(f"✅ {var}: {masked}")
        else:
            print(f"⚠️  {var}: Not set")
    
    print("\n💡 Security Recommendations:")
    print("1. Use environment variables for all secrets")
    print("2. Add .env files to .gitignore")
    print("3. Use AWS IAM roles instead of access keys")
    print("4. Regularly rotate JWT secrets")
    print("5. Monitor access patterns")
    
    return len(findings)

if __name__ == "__main__":
    issues_found = check_for_hardcoded_secrets()
    
    if issues_found > 0:
        print(f"\n❌ Found {issues_found} potential security issues.")
        print("Please review and fix these before deploying to production.")
        exit(1)
    else:
        print("\n✅ Security scan completed. No obvious issues found!")
        exit(0)