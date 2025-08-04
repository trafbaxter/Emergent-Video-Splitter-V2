#!/usr/bin/env python3
"""
Check AWS SES setup and domain verification status
"""
import boto3
import os
from botocore.exceptions import ClientError

def check_ses_setup():
    """Check current SES configuration and setup"""
    
    # AWS credentials
    aws_access_key = 'REDACTED_AWS_KEY'
    aws_secret_key = 'kSLXhxXDBZjgxZF9nHZHG8cZKrHM6KrNKv4gCXBE'
    region = 'us-east-1'  # SES is typically in us-east-1 for global sending
    
    # Initialize SES client
    ses_client = boto3.client(
        'ses',
        region_name=region,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    
    print("🔍 Checking AWS SES Configuration...")
    
    try:
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
    success = check_ses_setup()
    
    if success:
        print("\n✅ SES setup check completed!")
    
    setup_domain_verification()