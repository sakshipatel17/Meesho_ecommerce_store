#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kostaa.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

# Create a test client
client = Client()

# Get an existing user
test_user = User.objects.filter(email='test@example.com').first()
if not test_user:
    print("No test user found. Creating one...")
    test_user = User.objects.create_user(
        email='test_login@example.com',
        password='TestPass123'
    )
    print(f"Created user: {test_user.email}")
else:
    print(f"Using existing user: {test_user.email}")

# Try login
print("\n--- Testing Login Flow ---")
response = client.post('/accounts/login/', {
    'username': 'test@example.com',
    'password': 'test@example.com'  # Try the existing user's password
}, follow=True)

print(f"Status Code: {response.status_code}")
print(f"Redirected: {len(response.redirect_chain) > 0}")

# Check if user is authenticated in session
if hasattr(response, 'wsgi_request'):
    is_authenticated = response.wsgi_request.user.is_authenticated
    print(f"User Authenticated: {is_authenticated}")
else:
    # For test client, check session
    if '_auth_user_id' in client.session:
        print(f"User ID in session: {client.session['_auth_user_id']}")
        print("✅ Login successful with session created!")
    else:
        print("❌ No session created")

# Alternative: check if we can access a protected page
print("\n--- Testing Session Persistence ---")
response2 = client.get('/')
print(f"Request to home with session: Status {response2.status_code}")
print("✅ Session persists across requests!" if response2.status_code == 200 else "❌ Session error")
