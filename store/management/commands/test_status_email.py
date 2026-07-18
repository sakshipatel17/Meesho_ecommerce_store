from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from store.models import Order, Product
from decimal import Decimal
import traceback

class Command(BaseCommand):
    help = 'Test order status update email by creating a new order and changing status'

    def handle(self, *args, **options):
        self.stdout.write('Testing order status update email...')
        
        try:
            # Get the correct User model
            User = get_user_model()
            
            # Get a product first
            product = Product.objects.first()
            if not product:
                self.stdout.write(self.style.ERROR('No products found. Create a product first.'))
                return
            
            print(f"🔍 DEBUG: Found product: {product.name}")
            
            # Get an existing user
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
                return
            
            print(f"🔍 DEBUG: Using existing user: {user.username} ({user.email})")
            
            # Create a new test order to avoid decimal issues
            print('🔍 DEBUG: Creating new test order...')
            order = Order.objects.create(
                customer=user,
                total_amount=Decimal('99.99'),  # Fresh decimal value
                name=getattr(user, 'name', '') or user.username,
                address='123 Test Street',
                city='Test City',
                state='Test State',
                pincode='123456',
                phone='1234567890',
                status='pending'  # Start with pending
            )
            order.products.add(product)
            
            print(f"🔍 DEBUG: New order created: {order.order_id}")
            print(f"🔍 DEBUG: Initial status: {order.status}")
            
            # Change order status to trigger email
            new_status = 'shipped'
            print(f"🔍 DEBUG: Changing status to: {new_status}")
            order.status = new_status
            order.save()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Order status changed to: {new_status}'))
            self.stdout.write('Check console for signal debug messages')
            self.stdout.write('Check customer email for status update notification')
            
        except Exception as e:
            print(f"🔍 DEBUG: Full error: {str(e)}")
            print(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
