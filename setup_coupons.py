#!/usr/bin/env python
"""
Quick setup script for creating initial coupons
Run this in Django shell: python manage.py shell < setup_coupons.py
"""

from store.models import Coupon

print("Creating initial coupons...")

# First-order discount
coupon1, created = Coupon.objects.get_or_create(
    code='FIRST10',
    defaults={
        'discount_type': 'percentage',
        'discount_value': 10.0,
        'is_for_first_order': True,
        'usage_limit_per_user': 1,
        'min_order_amount': 0.0,
        'is_active': True
    }
)
print(f"✅ FIRST10: {'Created' if created else 'Already exists'}")

# General 20% discount
coupon2, created = Coupon.objects.get_or_create(
    code='SAVE20',
    defaults={
        'discount_type': 'percentage',
        'discount_value': 20.0,
        'is_for_first_order': False,
        'usage_limit_per_user': 1,
        'min_order_amount': 1000.0,
        'is_active': True
    }
)
print(f"✅ SAVE20: {'Created' if created else 'Already exists'}")

# Flat ₹100 off
coupon3, created = Coupon.objects.get_or_create(
    code='FLAT100',
    defaults={
        'discount_type': 'fixed',
        'discount_value': 100.0,
        'is_for_first_order': False,
        'usage_limit_per_user': 1,
        'min_order_amount': 500.0,
        'is_active': True
    }
)
print(f"✅ FLAT100: {'Created' if created else 'Already exists'}")

# Premium coupon
coupon4, created = Coupon.objects.get_or_create(
    code='PREMIUM25',
    defaults={
        'discount_type': 'percentage',
        'discount_value': 25.0,
        'is_for_first_order': False,
        'usage_limit_per_user': 1,
        'min_order_amount': 2000.0,
        'is_active': True
    }
)
print(f"✅ PREMIUM25: {'Created' if created else 'Already exists'}")

# Meesho special
coupon5, created = Coupon.objects.get_or_create(
    code='MEESHO15',
    defaults={
        'discount_type': 'percentage',
        'discount_value': 15.0,
        'is_for_first_order': False,
        'usage_limit_per_user': 2,  # Can use twice
        'min_order_amount': 0.0,
        'is_active': True
    }
)
print(f"✅ MEESHO15: {'Created' if created else 'Already exists'}")

# 10% general discount
coupon6, created = Coupon.objects.get_or_create(
    code='SAVE10',
    defaults={
        'discount_type': 'percentage',
        'discount_value': 10.0,
        'is_for_first_order': False,
        'usage_limit_per_user': 1,
        'min_order_amount': 0.0,
        'is_active': True
    }
)
print(f"✅ SAVE10: {'Created' if created else 'Already exists'}")

print("\n✨ Coupon setup complete!")
print("\nAvailable coupons:")
for coupon in Coupon.objects.filter(is_active=True).order_by('code'):
    coupon_type = f"{coupon.discount_value}%" if coupon.discount_type == 'percentage' else f"₹{coupon.discount_value}"
    first_order = " (First Order)" if coupon.is_for_first_order else ""
    min_order = f" | Min Order: ₹{coupon.min_order_amount}" if coupon.min_order_amount > 0 else ""
    print(f"  • {coupon.code}: {coupon_type}{first_order}{min_order}")

print("\n📊 Total active coupons:", Coupon.objects.filter(is_active=True).count())
