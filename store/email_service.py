"""
Enhanced Email Service for Order Notifications
Handles all order lifecycle emails with HTML templates
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Order


def send_order_email(user, order, email_type):
    """
    Send order-related emails based on type
    
    Args:
        user: User object
        order: Order object
        email_type: Type of email (placed, dispatched, delivered, cancelled)
    """
    try:
        # Define email templates and subjects
        email_config = {
            'placed': {
                'template': 'emails/order_placed.html',
                'subject': f'🛒 Order Confirmed - #{order.order_id}',
            },
            'dispatched': {
                'template': 'emails/order_dispatched.html',
                'subject': f'🚚 Order Dispatched - #{order.order_id}',
            },
            'delivered': {
                'template': 'emails/order_delivered.html',
                'subject': f'✅ Order Delivered - #{order.order_id}',
            },
            'cancelled': {
                'template': 'emails/order_cancelled.html',
                'subject': f'❌ Order Cancelled - #{order.order_id}',
            }
        }
        
        if email_type not in email_config:
            return False
        
        config = email_config[email_type]
        
        # Render HTML template
        html_content = render_to_string(
            config['template'],
            {
                'user': user,
                'order': order,
            }
        )
        
        # Plain text version
        plain_text = f"""
        Order {email_type.title()} - #{order.order_id}
        
        Dear {user.name or user.email},
        
        Your order status has been updated to: {order.get_status_display()}
        
        Order ID: {order.order_id}
        Tracking ID: {order.tracking_id}
        Total Amount: ₹{order.total_amount}
        
        Thank you for shopping with Kostaa Store.
        """
        
        # Send email
        send_mail(
            subject=config['subject'],
            message=plain_text,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER),
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"Error sending {email_type} email: {str(e)}")
        return False


def send_order_confirmation(user, order):
    """Send order confirmation email"""
    return send_order_email(user, order, 'placed')


def send_order_dispatched(user, order):
    """Send order dispatched email"""
    return send_order_email(user, order, 'dispatched')


def send_order_delivered(user, order):
    """Send order delivered email"""
    return send_order_email(user, order, 'delivered')


def send_order_cancelled(user, order):
    """Send order cancelled email"""
    return send_order_email(user, order, 'cancelled')
