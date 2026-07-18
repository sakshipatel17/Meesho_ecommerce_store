#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kostaa.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from store.models import Product, Cart, CartItem

User = get_user_model()

# Create a test client
client = Client()

# Get a test user
try:
    user = User.objects.get(email='test@example.com')
except User.DoesNotExist:
    print("Test user not found")
    exit(1)

# Get a product
try:
    product = Product.objects.first()
except:
    print("No products found")
    exit(1)

print(f"Testing with user: {user.email}")
print(f"Testing with product: {product.name if product else 'None'}")

if not product:
    print("No products in database")
    exit(1)

# Login the user
client.force_login(user)
print(f"✅ User logged in")

# Clear any existing cart
Cart.objects.filter(user=user).delete()
CartItem.objects.filter(cart__user=user).delete()

# Test add_to_cart
print(f"\n--- Testing Add to Cart ---")
try:
    response = client.get(f'/add-to-cart/{product.id}/')
    print(f"Status Code: {response.status_code}")
    
    # Check if cart was created
    cart = Cart.objects.get(user=user)
    cart_items = CartItem.objects.filter(cart=cart)
    print(f"✅ Cart created with {cart_items.count()} items")
    
    # Try adding same product again
    response2 = client.get(f'/add-to-cart/{product.id}/')
    cart_items = CartItem.objects.filter(cart=cart)
    
    if cart_items.count() > 0:
        item = cart_items.first()
        print(f"✅ Product quantity: {item.quantity}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Add to Cart Test Complete!")
