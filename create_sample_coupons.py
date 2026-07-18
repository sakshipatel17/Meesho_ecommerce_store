#!/usr/bin/env python
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kostaa.settings')
django.setup()

from store.models import Coupon

def create_sample_coupons():
    """Create sample coupons for testing"""
    print("🎫 CREATING SAMPLE COUPONS")
    print("=" * 50)
    
    # Sample coupons data
    coupons_data = [
        {
            'code': 'SAVE20',
            'discount_type': 'percentage',
            'discount_value': 20,
            'min_order_amount': 0,
            'is_for_first_order': False,
            'usage_limit_per_user': 3,
            'is_active': True
        },
        {
            'code': 'FIRST10',
            'discount_type': 'percentage',
            'discount_value': 10,
            'min_order_amount': 0,
            'is_for_first_order': True,
            'usage_limit_per_user': 1,
            'is_active': True
        },
        {
            'code': 'FLAT100',
            'discount_type': 'fixed',
            'discount_value': 100,
            'min_order_amount': 500,
            'is_for_first_order': False,
            'usage_limit_per_user': 2,
            'is_active': True
        },
        {
            'code': 'PREMIUM25',
            'discount_type': 'percentage',
            'discount_value': 25,
            'min_order_amount': 1000,
            'is_for_first_order': False,
            'usage_limit_per_user': 1,
            'is_active': True
        },
        {
            'code': 'MEESHO15',
            'discount_type': 'percentage',
            'discount_value': 15,
            'min_order_amount': 300,
            'is_for_first_order': False,
            'usage_limit_per_user': 5,
            'is_active': True
        },
        {
            'code': 'SAVE15',
            'discount_type': 'percentage',
            'discount_value': 15,
            'min_order_amount': 200,
            'is_for_first_order': False,
            'usage_limit_per_user': 3,
            'is_active': True
        },
        {
            'code': 'FLAT50',
            'discount_type': 'fixed',
            'discount_value': 50,
            'min_order_amount': 250,
            'is_for_first_order': False,
            'usage_limit_per_user': 2,
            'is_active': True
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for coupon_data in coupons_data:
        coupon, created = Coupon.objects.update_or_create(
            code=coupon_data['code'],
            defaults=coupon_data
        )
        
        if created:
            print(f"✅ Created: {coupon.code} - {coupon.discount_value}% off" if coupon.discount_type == 'percentage' else f"✅ Created: {coupon.code} - ₹{coupon.discount_value} off")
            created_count += 1
        else:
            print(f"🔄 Updated: {coupon.code}")
            updated_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 SUMMARY:")
    print(f"   New coupons created: {created_count}")
    print(f"   Existing coupons updated: {updated_count}")
    print(f"   Total coupons in database: {Coupon.objects.count()}")
    
    print("\n🎯 AVAILABLE COUPONS:")
    all_coupons = Coupon.objects.all()
    for coupon in all_coupons:
        if coupon.is_active:
            if coupon.discount_type == 'percentage':
                display = f"{coupon.code} - {coupon.discount_value}% off"
            else:
                display = f"{coupon.code} - ₹{coupon.discount_value} off"
            
            if coupon.is_for_first_order:
                display += " (First Order Only)"
            
            if coupon.min_order_amount > 0:
                display += f" (Min: ₹{coupon.min_order_amount})"
            
            print(f"   🎫 {display}")
    
    print("\n🎉 COUPON SYSTEM READY!")
    print("Now test your checkout page to see the dropdown working!")

if __name__ == "__main__":
    create_sample_coupons()
