# Generated migration for adding tracking_id field (Fixed for MongoDB/Djongo)

from django.db import migrations, models
import uuid


def generate_tracking_ids(apps, schema_editor):
    """Generate tracking IDs for existing orders using raw update to avoid save() issues"""
    Order = apps.get_model('store', 'Order')
    
    # Get all orders without tracking_id
    orders_without_tracking = Order.objects.filter(tracking_id__isnull=True)
    
    # Bulk update with tracking IDs (avoids calling save() which has Decimal128 issues)
    for order in orders_without_tracking:
        tracking_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        # Use update() instead of save() to avoid Decimal128 conversion issues
        Order.objects.filter(order_id=order.order_id).update(tracking_id=tracking_id)


def reverse_tracking_ids(apps, schema_editor):
    """Reverse: clear tracking IDs"""
    Order = apps.get_model('store', 'Order')
    Order.objects.all().update(tracking_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_auto_20260312_1324'),
    ]

    operations = [
        # First add field without unique constraint (nullable to avoid NULL conflict)
        migrations.AddField(
            model_name='order',
            name='tracking_id',
            field=models.CharField(
                blank=True, 
                help_text='Unique tracking ID for order', 
                max_length=20, 
                null=True,
                default=None
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='shipped_date',
            field=models.DateTimeField(blank=True, help_text='Date when order was dispatched', null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='delivered_date',
            field=models.DateTimeField(blank=True, help_text='Date when order was delivered', null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='estimated_delivery',
            field=models.DateField(blank=True, help_text='Estimated delivery date', null=True),
        ),
        # Populate existing records
        migrations.RunPython(generate_tracking_ids, reverse_tracking_ids),
    ]
