#!/usr/bin/env python
import os
import django

# Set up Django with console backend for testing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kostaa.settings')
django.setup()

# Temporarily use console backend
from django.conf import settings
settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

User = get_user_model()

# Test password reset with console backend
email = "sakshipatel07173@gmail.com"
user = User.objects.filter(email=email).first()

if user:
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_link = f"http://127.0.0.1:8000/password-reset/confirm/{uid}/{token}/"
    
    print("🖥️  CONSOLE BACKEND TEST")
    print("=" * 50)
    print("Password reset email content:")
    print("-" * 30)
    
    send_mail(
        'Password Reset Request',
        f'''
        Hello {user.username},
        
        Click here to reset password:
        {reset_link}
        
        This link expires in 24 hours.
        ''',
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )
    
    print("-" * 30)
    print("✅ If you see email content above, Django password reset works!")
    print("   The issue is Gmail SMTP configuration.")
else:
    print("❌ User not found")
