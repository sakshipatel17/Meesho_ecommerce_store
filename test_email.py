#!/usr/bin/env python
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kostaa.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

def test_email_config():
    """Test email configuration"""
    print("🔧 EMAIL CONFIGURATION CHECK")
    print("=" * 50)
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print("=" * 50)

def test_user_exists():
    """Check if user exists with the email"""
    print("\n👤 USER CHECK")
    print("=" * 50)
    email = "sakshipatel07173@gmail.com"
    users = User.objects.filter(email=email)
    
    if users.exists():
        print(f"✅ Found {users.count()} user(s) with email: {email}")
        for user in users:
            print(f"   - Username: {user.username}")
            print(f"   - Email: {user.email}")
            print(f"   - Active: {user.is_active}")
    else:
        print(f"❌ NO user found with email: {email}")
        print("   This is why password reset email is NOT sent!")
    print("=" * 50)

def test_send_email():
    """Test sending email"""
    print("\n📧 EMAIL SEND TEST")
    print("=" * 50)
    
    try:
        result = send_mail(
            'Test Password Reset Email',
            '''
            This is a test email for password reset functionality.
            
            If you receive this email, the email system is working!
            
            Test Link: http://127.0.0.1:8000/password-reset/confirm/test-token/
            ''',
            settings.EMAIL_HOST_USER,
            ['sakshipatel07173@gmail.com'],
            fail_silently=False,
        )
        
        if result == 1:
            print("✅ Email sent successfully!")
            print("   Check your inbox (and spam folder)")
        else:
            print(f"⚠️  Email send returned: {result}")
            
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        print("   Check your Gmail App Password configuration")
    
    print("=" * 50)

def test_password_reset_token():
    """Test password reset token generation"""
    print("\n🔑 PASSWORD RESET TOKEN TEST")
    print("=" * 50)
    
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    
    email = "sakshipatel07173@gmail.com"
    users = User.objects.filter(email=email)
    
    if users.exists():
        user = users.first()
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        reset_link = f"http://127.0.0.1:8000/password-reset/confirm/{uid}/{token}/"
        
        print(f"✅ Token generated for user: {user.username}")
        print(f"   UID: {uid}")
        print(f"   Token: {token}")
        print(f"   Reset Link: {reset_link}")
        
        # Try to send password reset email
        try:
            from django.core.mail import send_mail
            send_mail(
                'Password Reset Request',
                f'''
                Hello {user.username},
                
                You requested a password reset. Click the link below:
                
                {reset_link}
                
                This link will expire in 24 hours.
                ''',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            print("✅ Password reset email sent!")
        except Exception as e:
            print(f"❌ Password reset email failed: {e}")
    else:
        print("❌ No user found for token test")
    
    print("=" * 50)

if __name__ == "__main__":
    print("🚀 DJANGO PASSWORD RESET EMAIL DEBUG")
    print("=" * 60)
    
    test_email_config()
    test_user_exists()
    test_send_email()
    test_password_reset_token()
    
    print("\n📋 SUMMARY")
    print("=" * 50)
    print("1. If email config looks good ✅")
    print("2. If user exists ✅")
    print("3. If test email sends ✅")
    print("4. Then password reset should work! 🎉")
    print("\n💡 If emails don't arrive:")
    print("   - Check Gmail App Password")
    print("   - Check spam folder")
    print("   - Try console backend for debugging")
