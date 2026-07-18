#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kostaa.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from store.views import add_to_cart
from store.models import Product, Cart, CartItem

User = get_user_model()

# Get test user
try:
    user = User.objects.get(email='test@example.com')
except User.DoesNotExist:
    print("Test user not found")
    exit(1)

# Get product
try:
    product = Product.objects.first()
    if not product:
        print("No products in database")
        exit(1)
except Exception as e:
    print(f"Error fetching products: {e}")
    exit(1)

print(f"Testing with user: {user.email}")
print(f"Testing with product: {product.name}")

# Clear existing cart
Cart.objects.filter(user=user).delete()
CartItem.objects.filter(cart__user=user).delete()

# Create request
factory = RequestFactory()
request = factory.get(f'/add-to-cart/{product.id}/')
request.user = user
request.session = {}

print(f"\n--- Testing add_to_cart view directly ---")
try:
    # Call the view directly
    response = add_to_cart(request, product.id)
    print(f"✅ View executed successfully")
    print(f"Response status: {response.status_code}")
    
    # Check cart
    cart = Cart.objects.get(user=user)
    items = CartItem.objects.filter(cart=cart)
    print(f"✅ Cart created with {items.count()} item(s)")
    
    for item in items:
        print(f"  - {item.product.name}: Qty={item.quantity}, Subtotal=${item.subtotal}")
    
    # Try adding same product again
    print(f"\n--- Testing quantity increment ---")
    response2 = add_to_cart(request, product.id)
    items = CartItem.objects.filter(cart=cart)
    
    for item in items:
        if item.product.id == product.id:
            print(f"✅ Product quantity after 2nd add: {item.quantity}")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print(f"\n✅ Direct View Test Complete!")
