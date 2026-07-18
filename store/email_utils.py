from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string


def send_order_email(user_email, order_id, customer_name, order_total):
    """
    Send order confirmation email to user
    """
    subject = f"Order Placed Successfully - #{order_id}"
    
    message = f"""
    Hello {customer_name},

    Your order has been placed successfully!

    Order Details:
    • Order ID: {order_id}
    • Status: Confirmed
    • Total Amount: ₹{order_total}

    Thank you for shopping with us! ❤️

    Best regards,
    The Kostaa Team
    """

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        print(f"✅ Order confirmation email sent to {user_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending order email: {e}")
        return False


def send_processing_email(user_email, order_id, customer_name):
    """
    Send order processing email to user
    """
    subject = f"Order Processing - #{order_id}"
    
    message = f"""
    Hello {customer_name},

    Your order is now being processed!

    Order Details:
    • Order ID: {order_id}
    • Status: Processing

    We will notify you once shipped 🚚

    Best regards,
    The Kostaa Team
    """

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        print(f"✅ Order processing email sent to {user_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending processing email: {e}")
        return False


def send_order_html_email(user_email, order_id, customer_name, order_total, order_items):
    """
    Send HTML order confirmation email (Pro Level)
    """
    subject = f"Order Placed Successfully - #{order_id}"
    
    context = {
        'customer_name': customer_name,
        'order_id': order_id,
        'order_total': order_total,
        'order_items': order_items
    }
    
    html_message = render_to_string('store/email/order_confirmation.html', context)
    
    try:
        email = EmailMessage(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
        )
        email.content_subtype = "html"
        email.send()
        print(f"✅ HTML order confirmation email sent to {user_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending HTML order email: {e}")
        return False


def send_shipped_email(user_email, order_id, customer_name, tracking_id):
    """
    Send order shipped email
    """
    subject = f"Order Shipped - #{order_id}"
    
    message = f"""
    Hello {customer_name},

    Great news! Your order has been shipped!

    Order Details:
    • Order ID: {order_id}
    • Status: Shipped
    • Tracking ID: {tracking_id}

    Track your order: /orders/track/{tracking_id}/

    Your package will arrive soon! 📦

    Best regards,
    The Kostaa Team
    """

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        print(f"✅ Order shipped email sent to {user_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending shipped email: {e}")
        return False
