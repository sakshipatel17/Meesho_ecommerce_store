from django.core.mail import send_mail
from django.template.loader import render_to_string
from decouple import config
from .models import Coupon, CouponUsage, Order

def sendOrderEmail(context):
    msg_plain = render_to_string('email/email.txt',context)
    msg_html = render_to_string('email/order_placed.html',context)
    send_mail(
        'Your order has been placed',
        msg_plain,
        config("EMAIL_HOST_USER"),
        [context['email']],
        html_message=msg_html,
        fail_silently=False,
    )

# ============ SMART COUPON ELIGIBILITY LOGIC ============

def is_first_time_buyer(user):
    """Check if user is a first-time buyer"""
    return Order.objects.filter(customer=user, status='success').count() == 0

def get_coupon_usage_count(user, coupon):
    """Get how many times a user has used a specific coupon"""
    return CouponUsage.objects.filter(user=user, coupon=coupon).count()

def can_use_coupon(user, coupon_code, cart_total):
    """
    Check if user is eligible to use a coupon
    Returns: (is_eligible, message)
    """
    try:
        coupon = Coupon.objects.filter(code=coupon_code.upper()).first()
        if not coupon:
            return False, f"Invalid coupon code: '{coupon_code}'"
        if not coupon.is_active:
            return False, f"This coupon is not active"
    except Exception as e:
        return False, f"Invalid coupon code: '{coupon_code}'"
    
    # Check if coupon is for first order only
    if coupon.is_for_first_order:
        if not is_first_time_buyer(user):
            return False, "This coupon is only for first-time orders"
    
    # Check usage limit per user
    usage_count = get_coupon_usage_count(user, coupon)
    if usage_count >= coupon.usage_limit_per_user:
        return False, f"You have already used this coupon {coupon.usage_limit_per_user} time(s)"
    
    # Check minimum order amount
    if cart_total < coupon.min_order_amount:
        return False, f"Minimum order amount of ₹{coupon.min_order_amount} required"
    
    return True, "Coupon is valid"

def calculate_discount(coupon_code, cart_total):
    """
    Calculate discount amount for a coupon
    Returns: (discount_amount, message)
    """
    try:
        coupon = Coupon.objects.filter(code=coupon_code.upper()).first()
        if not coupon:
            return 0, "Invalid coupon code"
        if not coupon.is_active:
            return 0, "This coupon is not active"
    except Exception as e:
        return 0, "Invalid coupon code"
    
    # Ensure cart_total is float
    cart_total = float(cart_total)
    
    if coupon.discount_type == 'percentage':
        discount_amount = float(cart_total) * (float(coupon.discount_value) / 100)
    else:  # fixed
        discount_amount = float(coupon.discount_value)
    
    # Apply max discount limit if set
    if coupon.max_discount_amount and discount_amount > float(coupon.max_discount_amount):
        discount_amount = float(coupon.max_discount_amount)
    
    # Ensure discount doesn't exceed cart total
    if discount_amount > cart_total:
        discount_amount = cart_total
    
    return discount_amount, "Discount calculated successfully"

def get_eligible_coupons_for_user(user, cart_total):
    """
    Get list of all coupons for a user, marking them as eligible or not
    Returns list of coupon dicts with details
    """
    coupons_list = []
    
    is_first_buyer = is_first_time_buyer(user)
    
    # Fetch all coupons and filter in Python to avoid Djongo SQLDecodeError with boolean filters
    for coupon in Coupon.objects.all():

        if not coupon.is_active:
            continue
            
        # Default eligibility
        is_eligible = True
        ineligibility_reason = ""
            
        # Check if coupon is for first order only
        if coupon.is_for_first_order and not is_first_buyer:
            is_eligible = False
            ineligibility_reason = "Only for first order"
        
        # Check usage limit
        if is_eligible:
            usage_count = get_coupon_usage_count(user, coupon)
            if usage_count >= coupon.usage_limit_per_user:
                is_eligible = False
                ineligibility_reason = f"Used {coupon.usage_limit_per_user} time(s)"
        
        # Check minimum order amount
        if is_eligible and cart_total < coupon.min_order_amount:
            is_eligible = False
            ineligibility_reason = f"Min. ₹{coupon.min_order_amount} required"
        
        # Calculate discount
        discount_amount, _ = calculate_discount(coupon.code, cart_total)
        
        coupons_list.append({
            'code': coupon.code,
            'discount_type': coupon.discount_type,
            'discount_value': float(coupon.discount_value),
            'discount_amount': float(discount_amount),
            'is_for_first_order': coupon.is_for_first_order,
            'min_order_amount': float(coupon.min_order_amount),
            'is_eligible': is_eligible,
            'ineligibility_reason': ineligibility_reason,
        })
    
    return coupons_list

def track_coupon_usage(user, coupon_code, order):
    """
    Track coupon usage for a user
    Creates a CouponUsage record
    """
    try:
        coupon = Coupon.objects.filter(code=coupon_code.upper()).first()
        if coupon:
            CouponUsage.objects.create(
                coupon=coupon,
                user=user,
                order=order
            )
        return True
    except Exception as e:
        return False