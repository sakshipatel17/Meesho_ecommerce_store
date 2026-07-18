from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMessage


def send_order_status_email(user_email, order_id, status, customer_name=None, tracking_id=None, order_total=None):
    """
    Send order status update email based on status
    """
    status_messages = {
        'placed': {
            'subject': f"Order Placed Successfully - #{order_id}",
            'message': f"""
            Hello {customer_name or 'Customer'},

            Great news! Your order has been placed successfully.

            Order Details:
            • Order ID: {order_id}
            • Status: Confirmed
            • Total Amount: ₹{order_total or 'N/A'}

            Thank you for shopping with us! 🛍️

            Track your order: /orders/track/{order_id}/
            """,
            'template': 'order_placed'
        },
        'confirmed': {
            'subject': f"Order Confirmed - #{order_id}",
            'message': f"""
            Hello {customer_name or 'Customer'},

            Your order has been confirmed and is being processed.

            Order Details:
            • Order ID: {order_id}
            • Status: Confirmed
            • Total Amount: ₹{order_total or 'N/A'}

            We'll notify you once it's shipped.

            Track your order: /orders/track/{order_id}/
            """,
            'template': 'order_confirmed'
        },
        'dispatched': {
            'subject': f"Order Dispatched - #{order_id}",
            'message': f"""
            Hello {customer_name or 'Customer'},

            Your order has been dispatched from our warehouse!

            Order Details:
            • Order ID: {order_id}
            • Status: Dispatched
            • Next Step: Shipping

            Your package is on its way to the shipping partner.

            Track your order: /orders/track/{order_id}/
            """,
            'template': 'order_dispatched'
        },
        'shipped': {
            'subject': f"Order Shipped - #{order_id}",
            'message': f"""
            Hello {customer_name or 'Customer'},

            Exciting news! Your order has been shipped! 🚚

            Order Details:
            • Order ID: {order_id}
            • Status: Shipped
            • Tracking ID: {tracking_id or 'Available soon'}
            • Expected Delivery: 3-5 business days

            Track your package: /orders/track/{tracking_id or order_id}/

            You'll receive another email when it's delivered.
            """,
            'template': 'order_shipped'
        },
        'delivered': {
            'subject': f"Order Delivered - #{order_id}",
            'message': f"""
            Hello {customer_name or 'Customer'},

            Your order has been delivered successfully! 🎉

            Order Details:
            • Order ID: {order_id}
            • Status: Delivered
            • Delivered to: Your registered address

            Please rate your experience and products.

            Thank you for shopping with us! ⭐

            View your order: /orders/track/{order_id}/
            """,
            'template': 'order_delivered'
        },
        'cancelled': {
            'subject': f"Order Cancelled - #{order_id}",
            'message': f"""
            Hello {customer_name or 'Customer'},

            Your order has been cancelled as requested.

            Order Details:
            • Order ID: {order_id}
            • Status: Cancelled
            • Refund Amount: ₹{order_total or 'N/A'}

            Refund Information:
            • Refund will be processed within 3-5 business days
            • Refund will be credited to your original payment method

            If you didn't request this cancellation, please contact us immediately.

            Thank you for understanding.
            """,
            'template': 'order_cancelled'
        },
        'replaced': {
            'subject': f"Order Replaced - #{order_id}",
            'message': f"""
            Hello {customer_name or 'Customer'},

            Your order replacement has been processed.

            Order Details:
            • Order ID: {order_id}
            • Status: Replaced
            • Replacement Amount: ₹{order_total or 'N/A'}

            Your replacement order will be shipped within 24 hours.

            Track your replacement: /orders/track/{order_id}/

            Thank you for your patience.
            """,
            'template': 'order_replaced'
        }
    }
    
    # Get email details for the status
    email_data = status_messages.get(status.lower())
    if not email_data:
        return False
    
    # Send text email
    try:
        send_mail(
            email_data['subject'],
            email_data['message'],
            settings.EMAIL_HOST_USER,
            [user_email],
            fail_silently=False,
        )
        print(f"✅ {status.title()} email sent to {user_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending {status} email: {e}")
        return False


def send_html_order_status_email(user_email, order_id, status, customer_name=None, tracking_id=None, order_total=None):
    """
    Send HTML order status email (Professional version)
    """
    status_templates = {
        'placed': 'store/email/order_placed.html',
        'confirmed': 'store/email/order_confirmed.html',
        'dispatched': 'store/email/order_dispatched.html',
        'shipped': 'store/email/order_shipped.html',
        'delivered': 'store/email/order_delivered.html',
        'cancelled': 'store/email/order_cancelled.html',
        'replaced': 'store/email/order_replaced.html'
    }
    
    template_path = status_templates.get(status.lower())
    if not template_path:
        return False
    
    context = {
        'customer_name': customer_name or 'Customer',
        'order_id': order_id,
        'status': status.title(),
        'tracking_id': tracking_id,
        'order_total': order_total,
        'site_url': 'http://127.0.0.1:8000'
    }
    
    try:
        html_content = render_to_string(template_path, context)
        
        email = EmailMessage(
            f"Order {status.title()} - #{order_id}",
            html_content,
            settings.EMAIL_HOST_USER,
            [user_email],
        )
        email.content_subtype = "html"
        email.send()
        
        print(f"✅ HTML {status.title()} email sent to {user_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending HTML {status} email: {e}")
        return False


def send_order_notification(user_email, order_id, status, customer_name=None, tracking_id=None, order_total=None, use_html=False):
    """
    Main function to send order notification
    """
    if use_html:
        return send_html_order_status_email(user_email, order_id, status, customer_name, tracking_id, order_total)
    else:
        return send_order_status_email(user_email, order_id, status, customer_name, tracking_id, order_total)


# Individual email functions for specific use cases
def send_order_placed_email(user_email, order_id, customer_name, order_total):
    """Send order placed email"""
    return send_order_notification(user_email, order_id, 'placed', customer_name, None, order_total)


def send_order_cancelled_email(user_email, order_id, customer_name, order_total):
    """Send order cancelled email"""
    return send_order_notification(user_email, order_id, 'cancelled', customer_name, None, order_total)


def send_order_shipped_email(user_email, order_id, customer_name, tracking_id):
    """Send order shipped email"""
    return send_order_notification(user_email, order_id, 'shipped', customer_name, tracking_id, None)


def send_order_delivered_email(user_email, order_id, customer_name):
    """Send order delivered email"""
    return send_order_notification(user_email, order_id, 'delivered', customer_name, None, None)
