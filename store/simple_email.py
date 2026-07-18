from django.core.mail import send_mail
from django.conf import settings


def send_order_email(user_email, order_id):
    """
    Send order confirmation email to user
    """
    subject = f"Order Confirmed - #{order_id}"
    
    message = f"""
    Hello,

    Your order has been placed successfully.

    Order ID: {order_id}
    Status: Confirmed

    Thank you for shopping with us.
    """

    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user_email],
            fail_silently=False,
        )
        print(f"✅ Order confirmation email sent to {user_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending order email: {e}")
        return False


def send_processing_email(user_email, order_id):
    """
    Send order processing email to user
    """
    subject = f"Order Processing - #{order_id}"
    
    message = f"""
    Hello,

    Your order is being processed.

    Order ID: {order_id}
    Status: Processing

    We will notify you once shipped.
    """

    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user_email],
            fail_silently=False,
        )
        print(f"✅ Order processing email sent to {user_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending processing email: {e}")
        return False
