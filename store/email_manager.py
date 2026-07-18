"""
Email Manager for Order Notifications
Centralized email sending with HTML templates
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Order


class OrderEmailManager:
    """Centralized email management for order notifications"""
    
    # Email templates mapping
    EMAIL_TEMPLATES = {
        'order_placed': {
            'subject': 'Order Placed Successfully - Tracking ID: {tracking_id}',
            'template': 'emails/order_placed_myntra.html',
            'plain_template': 'emails/order_placed.txt',
        },
        'order_processing': {
            'subject': 'Your Order is Being Processed',
            'template': 'emails/order_processing_myntra.html',
            'plain_template': 'emails/order_status.txt',
        },
        'order_dispatched': {
            'subject': '🚚 Your Package is On Its Way! - {tracking_id}',
            'template': 'emails/order_dispatched_myntra.html',
            'plain_template': 'emails/order_dispatched.txt',
        },
        'order_out_for_delivery': {
            'subject': '📍 Your Order is Out for Delivery - {tracking_id}',
            'template': 'emails/order_out_for_delivery_myntra.html',
            'plain_template': 'emails/order_delivery.txt',
        },
        'order_delivered': {
            'subject': '✅ Your Order has been Delivered!',
            'template': 'emails/order_delivered_myntra.html',
            'plain_template': 'emails/order_delivered.txt',
        },
        'order_cancelled': {
            'subject': 'Order Cancelled - {order_id}',
            'template': 'emails/order_cancelled_myntra.html',
            'plain_template': 'emails/order_cancelled.txt',
        },
    }
    
    @staticmethod
    def send_order_email(user, order, email_type, additional_context=None):
        """
        Send order-related email
        
        Args:
            user: User object
            order: Order instance
            email_type: Type of email ('order_placed', 'order_dispatched', etc.)
            additional_context: Additional context data for template
        
        Returns:
            (success, message)
        """
        if not order.customer or not order.customer.email:
            return False, "User email not found"
        
        if email_type not in OrderEmailManager.EMAIL_TEMPLATES:
            return False, f"Unknown email type: {email_type}"
        
        template_config = OrderEmailManager.EMAIL_TEMPLATES[email_type]
        recipient_email = order.customer.email
        user = order.customer
        
        # Build context
        context = {
            'order': order,
            'user': user,
            'tracking_id': order.tracking_id,
            'order_id': order.order_id,
            'customer_name': user.name or user.email,
            'estimated_delivery': order.estimated_delivery or 'Within 7 days',
            'products': order.products.all(),
            'total_amount': order.total_amount,
            'discount_amount': order.discount_amount or 0,
            'shipping_charges': 0,  # Can be enhanced
            'payment_method': order.payment_method.upper() if order.payment_method else 'UNKNOWN',
        }
        
        # Merge additional context
        if additional_context:
            context.update(additional_context)
        
        # Prepare subject
        subject = template_config['subject'].format(
            tracking_id=order.tracking_id,
            order_id=order.order_id
        )
        
        # Render email templates
        try:
            # HTML template
            html_message = render_to_string(template_config['template'], context)
        except Exception as e:
            html_message = None
            print(f"HTML template error: {e}")
        
        try:
            # Plain text template
            plain_message = render_to_string(template_config['plain_template'], context)
        except Exception as e:
            plain_message = f"Order {order.order_id} - {email_type}"
        
        # Send email
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=config("EMAIL_USER", settings.DEFAULT_FROM_EMAIL),
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False,
            )
            return True, f"Email sent successfully to {recipient_email}"
        except Exception as e:
            print(f"Error sending email: {e}")
            return False, f"Error sending email: {str(e)}"
    
    @staticmethod
    def send_welcome_order_email(order):
        """Send order placed confirmation email"""
        return OrderEmailManager.send_order_email(order, 'order_placed')
    
    @staticmethod
    def send_processing_email(order):
        """Send processing notification email"""
        return OrderEmailManager.send_order_email(order, 'order_processing')
    
    @staticmethod
    def send_dispatched_email(order):
        """Send dispatched notification email"""
        return OrderEmailManager.send_order_email(order, 'order_dispatched')
    
    @staticmethod
    def send_out_for_delivery_email(order):
        """Send out for delivery notification email"""
        return OrderEmailManager.send_order_email(order, 'order_out_for_delivery')
    
    @staticmethod
    def send_delivered_email(order):
        """Send delivery confirmation email"""
        return OrderEmailManager.send_order_email(order, 'order_delivered')
    
    @staticmethod
    def send_cancelled_email(order, reason=''):
        """Send order cancellation email"""
        additional_context = {'reason': reason}
        return OrderEmailManager.send_order_email(order, 'order_cancelled', additional_context)
