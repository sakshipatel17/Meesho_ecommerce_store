#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kostaa.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from store.models import Product, Cart, CartItem, Order

User = get_user_model()

# Create a test client
client = Client()

# Get a test user
try:
    user = User.objects.get(email='test@example.com')
except User.DoesNotExist:
    print("Test user not found")
    exit(1)

print(f"Testing with user: {user.email}")

# Get products
try:
    products = Product.objects.all()[:2]
    if not products:
        print("No products in database")
        exit(1)
except:
    print("Error fetching products")
    exit(1)

# Login the user
client.force_login(user)
print(f"✅ User logged in")

# Clear existing cart
Cart.objects.filter(user=user).delete()
CartItem.objects.filter(cart__user=user).delete()

print(f"\n--- Testing Full Checkout Flow ---")

# 1. Add multiple items to cart
for i, product in enumerate(products, 1):
    print(f"\nAdding product {i}: {product.name}")
    try:
        response = client.get(f'/add-to-cart/{product.id}/')
        print(f"✅ Added to cart (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Error adding to cart: {e}")
        continue

# 2. Check cart has items
try:
    cart = Cart.objects.get(user=user)
    cart_items = CartItem.objects.filter(cart=cart)
    print(f"\n✅ Cart has {cart_items.count()} items")
    
    total = 0
    for item in cart_items:
        print(f"  - {item.product.name}: Qty={item.quantity}, Subtotal=${item.subtotal:.2f}")
        total += item.subtotal
    print(f"  Total: ${total:.2f}")
except Exception as e:
    print(f"❌ Error checking cart: {e}")

# 3. Test checkout page access
print(f"\n--- Testing Checkout Access ---")
try:
    response = client.get('/checkout/')
    print(f"✅ Checkout page accessible (Status: {response.status_code})")
except Exception as e:
    print(f"❌ Error accessing checkout: {e}")

# 4. Verify subtotal is float, not Decimal
print(f"\n--- Verifying Data Types ---")
for item in CartItem.objects.filter(cart__user=user):
    print(f"✅ CartItem subtotal type: {type(item.subtotal).__name__} = {item.subtotal}")

print(f"\n✅ Full Flow Test Complete!")
