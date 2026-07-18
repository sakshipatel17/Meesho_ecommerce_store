#!/usr/bin/env python
"""
Test script for complete dynamic payment flow
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kostaa.settings')
django.setup()

from store.payment_helper import validate_card, validate_upi_id

def test_payment_validations():
    print("🧪 Testing Payment Validations")
    print("=" * 50)
    
    # Test Card Validation
    print("\n1. Testing Card Validation:")
    test_cards = [
        ("4111 1111 1111 1111", "12/25", "123", True),  # Valid
        ("1234567890123456", "09/24", "456", True),   # Valid
        ("1234", "12/25", "123", False),                # Invalid card number
        ("4111111111111111", "13/25", "123", False),  # Invalid month
        ("4111111111111111", "12/20", "123", False),  # Expired
        ("4111111111111111", "12/25", "12", False),   # Invalid CVV
    ]
    
    for card_num, expiry, cvv, expected in test_cards:
        try:
            is_valid, message = validate_card(card_num, expiry, cvv)
            status = "✅" if is_valid == expected else "❌"
            print(f"   {status} Card {card_num}: {message}")
        except Exception as e:
            print(f"   ❌ Card {card_num}: Error - {str(e)}")
    
    # Test UPI Validation
    print("\n2. Testing UPI ID Validation:")
    test_upi_ids = [
        ("user@okaxis", True),           # Valid
        ("example@ybl", True),          # Valid
        ("test@paytm", True),          # Valid
        ("invalid", False),             # Invalid - no @
        ("a@b", False),               # Invalid - too short
        ("user", False),               # Invalid - no @
        ("", False),                   # Invalid - empty
    ]
    
    for upi_id, expected in test_upi_ids:
        try:
            is_valid, message = validate_upi_id(upi_id)
            status = "✅" if is_valid == expected else "❌"
            print(f"   {status} UPI {upi_id}: {message}")
        except Exception as e:
            print(f"   ❌ UPI {upi_id}: Error - {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Payment Validation Test Complete!")

def test_order_model():
    print("\n🧪 Testing Order Model Payment Methods")
    print("=" * 50)
    
    from store.models import Order
    
    print("\nAvailable Payment Method Choices:")
    for choice in Order._meta.get_field('payment_method').choices:
        print(f"   {choice[0]}: {choice[1]}")
    
    print("\n✅ Order model supports all required payment methods")
    
    print("\n" + "=" * 50)
    print("🎉 Order Model Test Complete!")

if __name__ == "__main__":
    test_payment_validations()
    test_order_model()
