from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from store.models import Order, Product
from decimal import Decimal
import traceback

class Command(BaseCommand):
    help = 'Test order signal by creating a test order'

    def handle(self, *args, **options):
        self.stdout.write('Testing order signal...')
        
        try:
            # Get the correct User model
            User = get_user_model()
            print(f"🔍 DEBUG: User model: {User}")
            
            # Get a product first
            product = Product.objects.first()
            if not product:
                self.stdout.write(self.style.ERROR('No products found. Create a product first.'))
                return
            
            print(f"🔍 DEBUG: Found product: {product.name}")
            
            # Try to get an existing user first
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
                return
            
            print(f"🔍 DEBUG: Using existing user: {user.username} ({user.email})")
            
            # Create a test order
            print('🔍 DEBUG: Creating test order...')
            order = Order.objects.create(
                customer=user,
                total_amount=Decimal('99.99'),
                name=getattr(user, 'name', '') or user.username,
                address='123 Test Street',
                city='Test City',
                state='Test State',
                pincode='123456',
                phone='1234567890'
            )
            order.products.add(product)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Test order created: {order.order_id}'))
            self.stdout.write('Check console for signal debug messages')
            
        except Exception as e:
            print(f"🔍 DEBUG: Full error: {str(e)}")
            print(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
