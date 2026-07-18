#!/usr/bin/env python
"""
Test script for dynamic QR code generation
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kostaa.settings')
django.setup()

from store.payment_helper import generate_upi_qr_code, generate_paytm_qr_code

def test_qr_generation():
    print("🧪 Testing Dynamic QR Code Generation")
    print("=" * 50)
    
    # Test UPI QR code generation
    print("\n1. Testing UPI QR Code Generation:")
    try:
        upi_qr = generate_upi_qr_code(299.99)
        print(f"✅ UPI QR Code generated successfully")
        print(f"   Type: {type(upi_qr)}")
        print(f"   Length: {len(upi_qr)} characters")
        if upi_qr.startswith('data:image'):
            print("   ✅ QR Code is in base64 format")
        else:
            print("   ⚠️  QR Code is fallback static image")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test Paytm QR code generation
    print("\n2. Testing Paytm QR Code Generation:")
    try:
        paytm_qr = generate_paytm_qr_code(499.99)
        print(f"✅ Paytm QR Code generated successfully")
        print(f"   Type: {type(paytm_qr)}")
        print(f"   Length: {len(paytm_qr)} characters")
        if paytm_qr.startswith('data:image'):
            print("   ✅ QR Code is in base64 format")
        else:
            print("   ⚠️  QR Code is fallback static image")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test with different amounts
    print("\n3. Testing with Different Amounts:")
    amounts = [0, 99, 999.99, 1500]
    for amount in amounts:
        try:
            upi_qr = generate_upi_qr_code(amount)
            paytm_qr = generate_paytm_qr_code(amount)
            print(f"   ✅ Amount ₹{amount}: UPI and Paytm QR codes generated")
        except Exception as e:
            print(f"   ❌ Amount ₹{amount}: Error - {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 QR Code Generation Test Complete!")

if __name__ == "__main__":
    test_qr_generation()
