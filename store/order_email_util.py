from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def test_email_configuration():
    """
    Test email configuration by sending a simple test email
    """
    print("🔍 DEBUG: Testing email configuration...")
    print(f"🔍 DEBUG: Email backend: {settings.EMAIL_BACKEND}")
    print(f"🔍 DEBUG: Email host: {settings.EMAIL_HOST}")
    print(f"🔍 DEBUG: Email port: {settings.EMAIL_PORT}")
    print(f"🔍 DEBUG: Email user: {settings.EMAIL_HOST_USER}")
    print(f"🔍 DEBUG: TLS enabled: {settings.EMAIL_USE_TLS}")
    
    try:
        result = send_mail(
            subject="🧪 Test Email - Meesho Store",
            message="This is a test email to verify SMTP configuration is working correctly.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Send to self for testing
            fail_silently=False,
        )
        print(f"🔍 DEBUG: Test email send_mail returned: {result}")
        if result:
            print("✅ Test email sent successfully!")
        else:
            print("❌ Test email failed - send_mail returned None/False")
        return result
    except Exception as e:
        print(f"❌ Test email failed with error: {str(e)}")
        import traceback
        print(f"🔍 DEBUG: Full traceback: {traceback.format_exc()}")
        return False

def send_order_status_update_email(order, new_status):
    """
    Send order status update email to customer
    """
    print(f"🔍 DEBUG: send_order_status_update_email called for order {order.order_id}")
    print(f"🔍 DEBUG: New status: {new_status}")
    print(f"🔍 DEBUG: Customer email: {order.customer.email}")
    
    try:
        # Status-specific email content
        status_messages = {
            'processing': {
                'subject': f'Your Order {order.order_id} is Being Processed',
                'message': f'Great news! Your order {order.order_id} is now being processed and will be shipped soon.',
                'emoji': '⚡'
            },
            'shipped': {
                'subject': f'Your Order {order.order_id} Has Been Shipped!',
                'message': f'Exciting news! Your order {order.order_id} has been shipped and is on its way to you.',
                'emoji': '📦'
            },
            'delivered': {
                'subject': f'Your Order {order.order_id} Has Been Delivered!',
                'message': f'Happy to inform you that your order {order.order_id} has been successfully delivered.',
                'emoji': '🎉'
            },
            'cancelled': {
                'subject': f'Your Order {order.order_id} Has Been Cancelled',
                'message': f'We regret to inform you that your order {order.order_id} has been cancelled.',
                'emoji': '❌'
            },
            'return_requested': {
                'subject': f'Return Request for Order {order.order_id}',
                'message': f'We have received your return request for order {order.order_id}. Our team will process it soon.',
                'emoji': '🔄'
            }
        }
        
        # Get status-specific content
        status_info = status_messages.get(new_status, {
            'subject': f'Update for Your Order {order.order_id}',
            'message': f'Your order {order.order_id} status has been updated to: {new_status}.',
            'emoji': '📋'
        })
        
        # Prepare email context
        context = {
            'order': order,
            'customer_name': getattr(order.customer, 'name', '') or order.customer.username,
            'order_id': order.order_id,
            'tracking_id': order.tracking_id,
            'new_status': new_status,
            'status_display': order.get_status_display(),
            'emoji': status_info['emoji'],
            'message': status_info['message'],
            'order_date': order.created_at.strftime('%d %B %Y'),
        }
        
        print(f"🔍 DEBUG: Status email context prepared")
        
        # Render email templates
        subject = status_info['subject']
        html_message = render_to_string('store/email/order_status_update.html', context)
        plain_message = render_to_string('store/email/order_status_update.txt', context)
        
        print(f"🔍 DEBUG: Status email templates rendered successfully")
        print(f"🔍 DEBUG: Subject: {subject}")
        print(f"🔍 DEBUG: Recipient: {order.customer.email}")
        
        # Send email
        print(f"🔍 DEBUG: Attempting to send status update email...")
        result = send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"🔍 DEBUG: Status update send_mail returned: {result}")
        logger.info(f"Order status update email sent successfully for order {order.order_id}")
        return True
        
    except Exception as e:
        print(f"🔍 DEBUG: Status update email sending failed with error: {str(e)}")
        print(f"🔍 DEBUG: Error type: {type(e).__name__}")
        import traceback
        print(f"🔍 DEBUG: Full traceback: {traceback.format_exc()}")
        logger.error(f"Failed to send order status update email for order {order.order_id}: {str(e)}")
        return False

def send_order_confirmation_email(order):
    """
    Send order confirmation email to customer
    """
    print(f"🔍 DEBUG: send_order_confirmation_email called for order {order.order_id}")
    print(f"🔍 DEBUG: Customer email: {order.customer.email}")
    print(f"🔍 DEBUG: Email settings - HOST: {settings.EMAIL_HOST}, PORT: {settings.EMAIL_PORT}")
    print(f"🔍 DEBUG: Email user: {settings.EMAIL_HOST_USER}")
    print(f"🔍 DEBUG: Email backend: {settings.EMAIL_BACKEND}")
    
    try:
        # Prepare email context
        context = {
            'order': order,
            'customer_name': getattr(order.customer, 'name', '') or order.customer.username,
            'order_id': order.order_id,
            'tracking_id': order.tracking_id,
            'products': order.products.all(),
            'total_amount': order.total_amount,
            'delivery_address': f"{order.address}, {order.city}, {order.state} - {order.pincode}",
            'order_date': order.created_at.strftime('%d %B %Y'),
            'payment_method': order.get_payment_method_display(),
        }
        
        print(f"🔍 DEBUG: Email context prepared with {len(context)} variables")
        
        # Render email templates
        subject = f"Order Confirmation - {order.order_id}"
        html_message = render_to_string('store/email/order_confirmation.html', context)
        plain_message = render_to_string('store/email/order_confirmation.txt', context)
        
        print(f"🔍 DEBUG: Email templates rendered successfully")
        print(f"🔍 DEBUG: Subject: {subject}")
        print(f"🔍 DEBUG: Recipient: {order.customer.email}")
        
        # Send email
        print(f"🔍 DEBUG: Attempting to send email...")
        result = send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"🔍 DEBUG: send_mail returned: {result}")
        logger.info(f"Order confirmation email sent successfully for order {order.order_id}")
        return True
        
    except Exception as e:
        print(f"🔍 DEBUG: Email sending failed with error: {str(e)}")
        print(f"🔍 DEBUG: Error type: {type(e).__name__}")
        import traceback
        print(f"🔍 DEBUG: Full traceback: {traceback.format_exc()}")
        logger.error(f"Failed to send order confirmation email for order {order.order_id}: {str(e)}")
        return False
