import sys
import os
sys.path.append('.')

from app.utils.email_service import email_service

def test_email():
    try:
        print("Testing email service...")
        print("Sending verification code to jan@binge.de")
        print(f"SMTP Server: {email_service.smtp_server}")
        print(f"SMTP Username: {email_service.username}")
        print(f"From Email: {email_service.from_email}")
        
        # Send test verification email
        result = email_service.send_verification_code('jan@binge.de', '123456', 'Jan')
        
        if result:
            print("✅ Email sent successfully!")
            print("Check jan@binge.de for the verification code: 123456")
        else:
            print("❌ Failed to send email")
            
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email() 