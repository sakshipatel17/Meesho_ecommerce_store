#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kostaa.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

# Check existing users
print("Existing users:")
for user in User.objects.all():
    print(f"  - {user.email}")

# Create a test client
client = Client()

# Try a POST request to login
print("\nAttempting login...")
try:
    response = client.post('/accounts/login/', {
        'username': 'test@example.com',
        'password': 'testpass123'
    })
    print(f"Status Code: {response.status_code}")
    print("Login successful!")
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
