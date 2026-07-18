
"""
Order Management Views
Handle order tracking, status updates, and lifecycle management
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import Order
from .order_lifecycle import OrderLifecycle
from .email_manager import OrderEmailManager


@login_required
def order_tracking(request, order_id):
    """Display order tracking page with full timeline and details"""
    from django.utils import timezone
    
    order = get_object_or_404(Order, order_id=order_id, customer=request.user)
    
    # Define timeline steps based on order status
    timeline_steps = []
    
    # Order Placed (always present)
    timeline_steps.append({
        'step': 'Order Placed',
        'status': 'completed',
        'icon': '🛒',
        'title': 'Order Placed',
        'description': f'Your order was placed on {order.created_at.strftime("%B %d, %Y at %I:%M %p")}',
        'time': order.created_at,
        'color': '#28a745'
    })
    
    # Processing (if status is processing or higher)
    if order.status in ['processing', 'shipped', 'delivered']:
        timeline_steps.append({
            'step': 'Processing',
            'status': 'completed',
            'icon': '⚙️',
            'title': 'Order Processing',
            'description': 'Your order is being processed and prepared for shipment.',
            'time': order.created_at + timezone.timedelta(hours=2),  # Estimated
            'color': '#6c757d'
        })
    
    # Shipped
    if order.status in ['shipped', 'delivered']:
        shipped_date = order.shipped_date or (order.created_at + timezone.timedelta(days=2))
        timeline_steps.append({
            'step': 'Shipped',
            'status': 'completed' if order.status == 'shipped' else 'upcoming',
            'icon': '📦',
            'title': 'Order Shipped',
            'description': 'Your order is on the way and will reach you soon.',
            'time': shipped_date,
            'color': '#007bff' if order.status == 'shipped' else '#6c757d'
        })
    
    # Delivered
    if order.status == 'delivered':
        delivery_date_str = order.delivered_date.strftime("%B %d, %Y at %I:%M %p") if order.delivered_date else "Recently"
        timeline_steps.append({
            'step': 'Delivered',
            'status': 'completed',
            'icon': '✅',
            'title': 'Order Delivered',
            'description': f'Your order was successfully delivered on {delivery_date_str}',
            'time': order.delivered_date or timezone.now(),
            'color': '#28a745'
        })
    
    # Cancelled
    if order.status == 'cancelled':
        timeline_steps.append({
            'step': 'Cancelled',
            'status': 'completed',
            'icon': '❌',
            'title': 'Order Cancelled',
            'description': 'This order was cancelled as per your request.',
            'time': order.updated_at,  # When it was cancelled
            'color': '#dc3545'
        })
    
    # Return Requested
    if order.status == 'return_requested':
        timeline_steps.append({
            'step': 'Return Requested',
            'status': 'completed',
            'icon': '🔄',
            'title': 'Return Requested',
            'description': 'Your return request has been received and is being processed.',
            'time': order.updated_at,
            'color': '#17a2b8'
        })
    
    context = {
        'order': order,
        'timeline_steps': timeline_steps,
        'current_status': order.get_status_display(),
        'progress_percentage': get_progress_percentage(order.status)
    }
    
    return render(request, 'store/order_tracking.html', context)


def get_progress_percentage(status):
    """Calculate progress percentage based on order status"""
    status_mapping = {
        'pending': 10,
        'processing': 25,
        'shipped': 75,
        'delivered': 100,
        'cancelled': 0,
        'return_requested': 50
    }
    return status_mapping.get(status, 0)
    
    # Get timeline progress
    timeline_data = OrderLifecycle.get_timeline_progress(order.status)
    
    # Prepare order context
    context = {
        'order': order,
        'timeline': timeline_data,
        'estimated_delivery': OrderLifecycle.get_estimated_delivery_date(order),
        'products': order.products.all(),
        'status_display': order.get_status_display(),
    }
    
    return render(request, 'store/order_tracking.html', context)


@login_required
def order_details(request, order_id):
    """Display detailed order information"""
    order = get_object_or_404(Order, order_id=order_id, customer=request.user)
    
    timeline_data = OrderLifecycle.get_timeline_progress(order.status)
    
    context = {
        'order': order,
        'timeline': timeline_data,
        'products': order.products.all(),
        'can_cancel': order.status in ['pending', 'processing'],
        'can_modify': order.status in ['pending'],
    }
    
    return render(request, 'store/order_details.html', context)


@login_required
def my_orders(request):
    """Display all orders for logged-in user"""
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    
    # Enrich with timeline data
    orders_with_timeline = []
    for order in orders:
        timeline = OrderLifecycle.get_timeline_progress(order.status)
        orders_with_timeline.append({
            'order': order,
            'timeline': timeline,
            'estimated_delivery': OrderLifecycle.get_estimated_delivery_date(order),
        })
    
    context = {
        'orders': orders_with_timeline,
        'total_orders': orders.count(),
    }
    
    return render(request, 'store/my_orders.html', context)


@require_http_methods(["POST"])
@login_required
def cancel_order(request, order_id):
    """Cancel an order (only if in pending or processing state)"""
    order = get_object_or_404(Order, order_id=order_id, customer=request.user)
    
    # Check if order can be cancelled
    if order.status not in ['pending', 'processing']:
        messages.error(request, 'This order cannot be cancelled.')
        return redirect('order_details', order_id=order_id)
    
    # Cancel the order
    reason = request.POST.get('reason', 'Customer requested cancellation')
    success, message = OrderLifecycle.transition_order(order, 'cancelled')
    
    if success:
        # Send cancellation email
        OrderEmailManager.send_cancelled_email(order, reason)
        messages.success(request, 'Order cancelled successfully. Refund will be processed within 3-5 days.')
    else:
        messages.error(request, message)
    
    return redirect('my_orders')


@require_http_methods(["POST"])
def update_order_status(request, order_id):
    """
    Admin endpoint to update order status (for admin dashboard)
    Requires admin authentication
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    order = get_object_or_404(Order, order_id=order_id)
    new_status = request.POST.get('status', '').lower()
    email_notification = request.POST.get('notify', 'true').lower() == 'true'
    
    # Transition order
    success, message = OrderLifecycle.transition_order(order, new_status, admin_action=True)
    
    if success:
        # Send notification email if requested
        if email_notification:
            email_map = {
                'processing': OrderEmailManager.send_processing_email,
                'dispatched': OrderEmailManager.send_dispatched_email,
                'out_for_delivery': OrderEmailManager.send_out_for_delivery_email,
                'delivered': OrderEmailManager.send_delivered_email,
                'cancelled': lambda o: OrderEmailManager.send_cancelled_email(o, 'Admin cancelled'),
            }
            
            if new_status in email_map:
                email_map[new_status](order)
        
        return JsonResponse({
            'success': True,
            'message': message,
            'new_status': order.status,
        })
    else:
        return JsonResponse({
            'success': False,
            'message': message,
        }, status=400)


@login_required
def resend_order_email(request, order_id):
    """Resend order status email"""
    order = get_object_or_404(Order, order_id=order_id, customer=request.user)
    
    # Map current status to email function
    email_map = {
        'pending': OrderEmailManager.send_order_email,
        'processing': OrderEmailManager.send_processing_email,
        'dispatched': OrderEmailManager.send_dispatched_email,
        'out_for_delivery': OrderEmailManager.send_out_for_delivery_email,
        'delivered': OrderEmailManager.send_delivered_email,
        'cancelled': lambda o: OrderEmailManager.send_cancelled_email(o, ''),
        'success': OrderEmailManager.send_order_email,
    }
    
    status = order.status.lower() if order.status else 'pending'
    
    if status in email_map:
        success, message = email_map[status](order, 'order_placed' if status in ['pending', 'success'] else status)
        if success:
            messages.success(request, 'Email resent successfully!')
        else:
            messages.error(request, f'Error: {message}')
    else:
        messages.warning(request, 'Unable to resend email for current order status.')
    
    return redirect('order_details', order_id=order_id)


def get_order_timeline_api(request, order_id):
    """API endpoint to get order timeline data (for dynamic updates)"""
    try:
        order = Order.objects.get(order_id=order_id)
        
        # Check authorization
        if request.user.is_authenticated and order.customer != request.user and not request.user.is_staff:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        timeline_data = OrderLifecycle.get_timeline_progress(order.status)
        
        return JsonResponse({
            'order_id': str(order.order_id),
            'tracking_id': order.tracking_id,
            'current_status': order.status,
            'timeline': timeline_data,
            'estimated_delivery': str(OrderLifecycle.get_estimated_delivery_date(order)) if OrderLifecycle.get_estimated_delivery_date(order) else None,
            'last_updated': order.updated_at.isoformat(),
        })
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
