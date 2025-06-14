#!/usr/bin/env python3
"""
Email delivery test script for WordBattle backend.
Use this to test email delivery to different addresses and diagnose issues.
"""

import sys
import os
import logging

# Add the app directory to Python path
sys.path.append('.')

def setup_logging():
    """Set up detailed logging for email testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_email_delivery(email: str, username: str = "TestUser"):
    """Test email delivery to a specific address."""
    try:
        from app.utils.email_service import email_service
        
        print(f"\n{'='*60}")
        print(f"Testing email delivery to: {email}")
        print(f"Username: {username}")
        print(f"{'='*60}")
        
        # Test verification code email
        verification_code = "123456"
        result = email_service.send_verification_code(email, verification_code, username)
        
        if result:
            print(f"✅ SUCCESS: Email sent to {email}")
            print(f"📧 Verification code: {verification_code}")
        else:
            print(f"❌ FAILED: Could not send email to {email}")
            print("Check the logs above for specific error details")
        
        return result
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False

def test_smtp_configuration():
    """Test SMTP configuration without sending emails."""
    try:
        from app.config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, FROM_EMAIL
        
        print(f"\n{'='*60}")
        print("SMTP Configuration Check")
        print(f"{'='*60}")
        print(f"SMTP Server: {SMTP_SERVER}")
        print(f"SMTP Port: {SMTP_PORT}")
        print(f"SMTP Username: {SMTP_USERNAME}")
        print(f"SMTP Password: {'***' if SMTP_PASSWORD else '(NOT SET)'}")
        print(f"From Email: {FROM_EMAIL}")
        
        if not SMTP_PASSWORD:
            print("⚠️  WARNING: SMTP_PASSWORD is not set!")
            return False
        
        print("✅ SMTP configuration appears complete")
        return True
        
    except Exception as e:
        print(f"❌ Error checking SMTP configuration: {e}")
        return False

def main():
    """Main test function."""
    setup_logging()
    
    print("WordBattle Email Delivery Test")
    print("=" * 60)
    
    # Test SMTP configuration first
    if not test_smtp_configuration():
        print("\n❌ SMTP configuration issues detected. Please fix before testing email delivery.")
        return
    
    # Test emails - you can modify these
    test_emails = [
        ("jan@binge.de", "Jan"),  # Real email that should work
        ("test@example.com", "TestUser"),  # Problematic domain
        # Add more test emails here
    ]
    
    successful_tests = 0
    total_tests = len(test_emails)
    
    for email, username in test_emails:
        try:
            success = test_email_delivery(email, username)
            if success:
                successful_tests += 1
        except KeyboardInterrupt:
            print("\n⚠️  Test interrupted by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error testing {email}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Test Results: {successful_tests}/{total_tests} emails sent successfully")
    
    if successful_tests == 0:
        print("❌ No emails were sent successfully. Check SMTP configuration and logs.")
    elif successful_tests < total_tests:
        print("⚠️  Some emails failed. This might be due to SMTP server policies.")
        print("   Real email addresses are more likely to work than test domains.")
    else:
        print("✅ All test emails sent successfully!")
    
    print("\nTips for troubleshooting:")
    print("- Test with real email addresses (avoid @example.com, @test.com)")
    print("- Check spam folders")
    print("- Verify SMTP server allows your domain to send emails")
    print("- Check email provider's logs if available")

if __name__ == "__main__":
    main() 