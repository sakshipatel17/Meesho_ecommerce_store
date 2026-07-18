#!/usr/bin/env python
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kostaa.settings')
django.setup()

# Temporarily change to console backend for debugging
from django.conf import settings
settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

User = get_user_model()

def test_console_email():
    """Test with console backend - shows output in terminal"""
    print("🖥️  CONSOLE EMAIL BACKEND TEST")
    print("=" * 60)
    print("Email output will appear below:")
    print("-" * 40)
    
    email = "sakshipatel07173@gmail.com"
    users = User.objects.filter(email=email)
    
    if users.exists():
        user = users.first()
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        reset_link = f"http://127.0.0.1:8000/password-reset/confirm/{uid}/{token}/"
        
        # Send password reset email
        send_mail(
            'Password Reset Request - Console Test',
            f'''
            Hello {user.username},
            
            You requested a password reset. Click the link below:
            
            {reset_link}
            
            This link will expire in 24 hours.
            
            If you see this in console, Django email system is working!
            The issue is with SMTP configuration.
            ''',
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
        
        print("-" * 40)
        print("✅ If you see email content above, Django password reset is working!")
        print("   The issue is with SMTP/Gmail configuration.")
        print("\n🔧 To fix SMTP:")
        print("   1. Use correct Gmail App Password")
        print("   2. Enable 2-Step Verification")
        print("   3. Generate new App Password")
        
    else:
        print("❌ No user found with email:", email)
        print("   Create user or check email spelling")

if __name__ == "__main__":
    test_console_email()
