#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kostaa.settings')

import django
from django.core.management import execute_from_command_line
from django.db import transaction

def fix_decimal_data():
    """Fix existing orders with comma-formatted decimal values"""
    from store.models import Order
    
    print("🔍 Fixing decimal data issues...")
    
    try:
        # Find orders with total_amount containing commas
        problematic_orders = Order.objects.filter(total_amount__contains=',')
        print(f"📊 Found {problematic_orders.count()} orders with comma-formatted totals")
        
        fixed_count = 0
        for order in problematic_orders:
            # Remove comma and convert to proper decimal
            old_amount = str(order.total_amount)
            if ',' in old_amount:
                new_amount = old_amount.replace(',', '')
                try:
                    from decimal import Decimal
                    order.total_amount = Decimal(new_amount)
                    order.save()
                    fixed_count += 1
                    print(f"✅ Fixed order {order.order_id}: {old_amount} → {new_amount}")
                except Exception as e:
                    print(f"❌ Error fixing order {order.order_id}: {e}")
        
        print(f"🎯 Fixed {fixed_count} orders successfully")
        
    except Exception as e:
        print(f"❌ Error fixing decimal data: {e}")

if __name__ == '__main__':
    fix_decimal_data()
