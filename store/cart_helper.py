"""
Cart Management Helper Functions
Handles cart persistence across login/logout sessions
"""
import json
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem, Product

def get_or_create_cart(user, session=None):
    """
    Get or create cart for user, merging session cart if exists
    """
    print(f"🛒 Getting/Creating cart for user: {user.email if user.is_authenticated else 'Anonymous'}")
    
    if user.is_authenticated:
        try:
            cart = Cart.objects.get(user=user)
            print(f"✅ Found existing cart for user: {cart.id}")
            
            # Merge session cart if exists
            if session and 'session_cart' in session:
                print("🔄 Merging session cart with user cart")
                merge_session_cart(cart, session)
                del session['session_cart']
            
            return cart
        except Cart.DoesNotExist:
            cart = Cart.objects.create(user=user)
            print(f"🆕 Created new cart for user: {cart.id}")
            
            # Merge session cart if exists
            if session and 'session_cart' in session:
                print("🔄 Merging session cart with new user cart")
                merge_session_cart(cart, session)
                del session['session_cart']
            
            return cart
    else:
        # For anonymous users, use session
        return None

def merge_session_cart(user_cart, session):
    """
    Merge session cart items into user cart
    """
    session_cart_data = session.get('session_cart', {})
    print(f"📦 Session cart data: {session_cart_data}")
    
    for product_id, quantity in session_cart_data.items():
        try:
            product = Product.objects.get(pk=product_id)
            
            # Manual pattern to avoid djongo get_or_create issues with UUID FK
            try:
                cart_item = CartItem.objects.get(cart=user_cart, product=product)
                cart_item.quantity += quantity
                cart_item.save()
            except CartItem.DoesNotExist:
                cart_item = CartItem(cart=user_cart, product=product, quantity=quantity)
                cart_item.save()
                
            print(f"✅ Merged product {product_id} with quantity {quantity}")
        except Product.DoesNotExist:
            print(f"❌ Product {product_id} not found during merge")
            continue

def add_to_session_cart(product_id, session, quantity=1):
    """
    Add item to session cart for anonymous users
    """
    if 'session_cart' not in session:
        session['session_cart'] = {}
    
    session_cart = session['session_cart']
    product_id = str(product_id)
    
    if product_id in session_cart:
        session_cart[product_id] += quantity
    else:
        session_cart[product_id] = quantity
    
    session.modified = True
    print(f"🛒 Added to session cart: product {product_id}, quantity {quantity}")

def remove_from_session_cart(product_id, session):
    """
    Remove item from session cart
    """
    if 'session_cart' in session:
        product_id = str(product_id)
        if product_id in session['session_cart']:
            del session['session_cart'][product_id]
            session.modified = True
            print(f"🗑️ Removed from session cart: product {product_id}")

def get_session_cart_items(session):
    """
    Get cart items from session
    """
    session_cart_data = session.get('session_cart', {})
    items = []
    
    for product_id, quantity in session_cart_data.items():
        try:
            product = Product.objects.get(pk=product_id)
            items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': float(product.price) * quantity
            })
        except Product.DoesNotExist:
            continue
    
    return items

def clear_session_cart(session):
    """
    Clear session cart
    """
    if 'session_cart' in session:
        del session['session_cart']
        session.modified = True
        print("🗑️ Cleared session cart")

def debug_cart_state(user, session):
    """
    Debug function to print cart state
    """
    print("🔍 DEBUG CART STATE:")
    print(f"User authenticated: {user.is_authenticated}")
    
    if user.is_authenticated:
        try:
            cart = Cart.objects.get(user=user)
            cart_items = CartItem.objects.filter(cart=cart)
            print(f"User cart items: {cart_items.count()}")
            for item in cart_items:
                print(f"  - Product: {item.product.name}, Qty: {item.quantity}")
        except Cart.DoesNotExist:
            print("No user cart found")
    
    if 'session_cart' in session:
        session_cart = session['session_cart']
        print(f"Session cart items: {len(session_cart)}")
        for product_id, quantity in session_cart.items():
            print(f"  - Product ID: {product_id}, Qty: {quantity}")
    else:
        print("No session cart found")
    
    print("=" * 50)
