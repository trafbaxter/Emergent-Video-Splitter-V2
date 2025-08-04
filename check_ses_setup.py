#!/usr/bin/env python3
"""
Check AWS SES setup and domain verification status
Note: This script now uses environment variables or AWS IAM roles for authentication
"""
import boto3
import os
from botocore.exceptions import ClientError

def check_ses_setup():
    """Check current SES configuration and setup"""
    
    # Use environment variables or AWS IAM roles for credentials
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    print("🔍 Checking AWS SES Configuration...")
    print(f"Region: {region}")
    
    try:
        # Initialize SES client (uses IAM role or environment credentials)
        ses_client = boto3.client('ses', region_name=region)
        
        # Check verified email addresses
        print("\n📧 Verified Email Addresses:")
        verified_emails = ses_client.list_verified_email_addresses()
        for email in verified_emails['VerifiedEmailAddresses']:
            print(f"  ✅ {email}")
        
        # Check verified domains
        print("\n🌐 Verified Domains:")
        identities = ses_client.list_identities()
        domains = [identity for identity in identities['Identities'] if '@' not in identity]
        
        for domain in domains:
            print(f"  ✅ {domain}")
            
            # Get domain verification status
            attrs = ses_client.get_identity_verification_attributes(Identities=[domain])
            status = attrs['VerificationAttributes'].get(domain, {}).get('VerificationStatus', 'Unknown')
            print(f"    Status: {status}")
        
        # Check sending statistics
        print("\n📊 Sending Statistics:")
        stats = ses_client.get_send_statistics()
        if stats['SendDataPoints']:
            latest = stats['SendDataPoints'][-1]
            print(f"  Sent: {latest.get('DeliveryAttempts', 0)}")
            print(f"  Bounces: {latest.get('Bounces', 0)}")
            print(f"  Complaints: {latest.get('Complaints', 0)}")
            print(f"  Rejects: {latest.get('Rejects', 0)}")
        else:
            print("  No sending statistics available")
        
        # Check sending quota
        print("\n📈 Sending Quota:")
        quota = ses_client.get_send_quota()
        print(f"  Daily quota: {quota['Max24HourSend']}")
        print(f"  Sent today: {quota['SentLast24Hours']}")
        print(f"  Send rate: {quota['MaxSendRate']} emails/second")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        print(f"❌ SES Error ({error_code}): {error_message}")
        
        if error_code == 'InvalidAccessKeyId':
            print("🔑 Invalid AWS Access Key ID")
        elif error_code == 'SignatureDoesNotMatch':
            print("🔑 Invalid AWS Secret Access Key")
        elif error_code == 'AccessDenied':
            print("🔑 Access denied - check IAM permissions for SES")
        
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def setup_domain_verification():
    """Guide for domain verification setup"""
    domain = "tads-video-splitter.com"
    
    print(f"\n📋 Domain Verification Setup for {domain}")
    print("="*50)
    print("To verify your domain in AWS SES:")
    print("1. Go to AWS SES Console")
    print("2. Click 'Verified identities' in the sidebar")
    print("3. Click 'Create identity'")
    print("4. Select 'Domain' and enter: tads-video-splitter.com")
    print("5. Add the TXT record to your DNS settings")
    print("6. Wait for verification (can take up to 72 hours)")
    print("\nOnce verified, you can send emails from any address @tads-video-splitter.com")

if __name__ == "__main__":
    print("🔐 Security Note: This script uses environment variables or IAM roles for AWS authentication")
    print("Set AWS_REGION environment variable if needed (defaults to us-east-1)")
    print()
    
    success = check_ses_setup()
    
    if success:
        print("\n✅ SES setup check completed!")
    
    setup_domain_verification()