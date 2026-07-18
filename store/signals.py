from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order
from .order_email_util import send_order_confirmation_email, send_order_status_update_email
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def order_status_change_notification(sender, instance, created, **kwargs):
    """
    Send email notification when order status changes or new order is created
    """
    if created:
        success = send_order_confirmation_email(instance)
        if success:
            logger.info(f"Order confirmation email sent successfully for order {instance.order_id}")
        else:
            logger.error(f"Failed to send order confirmation email for order {instance.order_id}")
    else:
        current_status = instance.status
        success = send_order_status_update_email(instance, current_status)
        if success:
            logger.info(f"Order status update email sent successfully for order {instance.order_id}")
        else:
            logger.error(f"Failed to send order status update email for order {instance.order_id}")


@receiver(pre_save, sender=Order)
def ensure_tracking_id(sender, instance, **kwargs):
    """Generate tracking ID before saving if not present"""
    if not instance.tracking_id:
        import uuid
        instance.tracking_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
