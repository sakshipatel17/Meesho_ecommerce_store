from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Order, CartItem, Product
from django.utils import timezone
from datetime import timedelta
from accounts.models import User


def get_date_range(filter_type):
    """Get start and end dates based on filter type"""
    now = timezone.now()
    
    if filter_type == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif filter_type == 'yesterday':
        yesterday = now - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif filter_type == 'last_7_days':
        start_date = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif filter_type == 'last_month':
        start_date = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        start_date = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return start_date, end_date


@require_GET
def analytics_kpis(request):
    """Get KPI data for analytics dashboard - MongoDB compatible version"""
    try:
        filter_type = request.GET.get('filter', 'last_7_days')
        
        # Get date range for filtering
        start_date, end_date = get_date_range(filter_type)
        
        # Get all orders and filter by date range and payment status in Python to avoid Djongo boolean field issues
        all_orders = list(Order.objects.all())
        
        # Filter orders by date range and payment status
        paid_orders_in_range = []
        for order in all_orders:
            if order.is_paid and order.created_at:
                if start_date <= order.created_at <= end_date:
                    paid_orders_in_range.append(order)
        
        # Count only paid orders in date range for dashboard metrics
        total_orders = len(paid_orders_in_range)
        
        # Get all cart items and sum quantities in Python
        cart_items = CartItem.objects.all()
        total_sales = sum(item.quantity for item in cart_items)
        
        # Calculate revenue from paid orders in date range only (handle Decimal128 from MongoDB)
        total_revenue = sum(float(str(order.total_amount)) for order in paid_orders_in_range if order.total_amount)
        
        # Payment methods - count from paid orders in date range only
        payment_methods = {}
        for order in paid_orders_in_range:
            method = order.payment_method or 'OTHER'
            payment_methods[method] = payment_methods.get(method, 0) + 1
        
        # Count all orders (paid and unpaid) in date range for payment status
        orders_in_range = []
        for order in all_orders:
            if order.created_at:
                if start_date <= order.created_at <= end_date:
                    orders_in_range.append(order)
        
        orders_paid = len(paid_orders_in_range)
        orders_unpaid = len(orders_in_range) - orders_paid
        
        # Total users (all registered users, not filtered by date)
        total_users = User.objects.count()
        
        data = {
            'total_orders': total_orders,
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'orders_paid': orders_paid,
            'orders_unpaid': orders_unpaid,
            'total_users': total_users,
            'payment_methods': [{'payment_method': k, 'count': v} for k, v in payment_methods.items()],
            'filter_type': filter_type,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'total_orders': 0,
            'total_sales': 0,
            'total_revenue': 0,
            'orders_paid': 0,
            'orders_unpaid': 0,
            'total_users': 0,
            'payment_methods': [],
            'filter_type': 'error',
            'date_range': {'start': '', 'end': ''}
        })


@require_GET
def sales_over_time(request):
    """Get sales data over time - MongoDB compatible version"""
    try:
        # Get all orders and filter in Python to avoid Djongo boolean field issues
        all_orders = list(Order.objects.all())
        paid_orders = [order for order in all_orders if order.is_paid]
        
        # Group by date in Python (paid orders only)
        sales_by_date = {}
        for order in paid_orders:
            date_str = order.created_at.strftime('%Y-%m-%d') if order.created_at else 'Unknown'
            if date_str not in sales_by_date:
                sales_by_date[date_str] = {'orders': 0, 'revenue': 0}
            sales_by_date[date_str]['orders'] += 1
            sales_by_date[date_str]['revenue'] += float(str(order.total_amount)) if order.total_amount else 0
        
        # Get last 7 days
        sorted_dates = sorted(sales_by_date.keys())[-7:]
        
        labels = sorted_dates
        orders_data = [sales_by_date[date]['orders'] for date in sorted_dates]
        revenue_data = [sales_by_date[date]['revenue'] for date in sorted_dates]
        
        return JsonResponse({
            'labels': labels,
            'orders': orders_data,
            'revenue': revenue_data
        })
    except Exception as e:
        return JsonResponse({
            'labels': [],
            'orders': [],
            'revenue': [],
            'error': str(e)
        })


@require_GET
def orders_vs_revenue(request):
    """Get orders vs revenue data - MongoDB compatible version"""
    try:
        # Get all orders and filter in Python to avoid Djongo boolean field issues
        all_orders = list(Order.objects.all())
        paid_orders = [order for order in all_orders if order.is_paid]
        
        # Group by date in Python (paid orders only)
        daily_data = {}
        for order in paid_orders:
            date_str = order.created_at.strftime('%b %d') if order.created_at else 'Unknown'
            if date_str not in daily_data:
                daily_data[date_str] = {'orders': 0, 'revenue': 0}
            daily_data[date_str]['orders'] += 1
            daily_data[date_str]['revenue'] += float(str(order.total_amount)) if order.total_amount else 0
        
        # Get last 7 days
        sorted_dates = sorted(daily_data.keys())[-7:]
        
        labels = sorted_dates
        orders = [daily_data[date]['orders'] for date in sorted_dates]
        revenue = [daily_data[date]['revenue'] for date in sorted_dates]
        
        return JsonResponse({
            'labels': labels,
            'orders': orders,
            'revenue': revenue
        })
    except Exception as e:
        return JsonResponse({
            'labels': [],
            'orders': [],
            'revenue': [],
            'error': str(e)
        })


@require_GET
def payment_methods_chart(request):
    """Get payment methods distribution - MongoDB compatible version"""
    try:
        # Get all orders and filter in Python to avoid Djongo boolean field issues
        all_orders = list(Order.objects.all())
        paid_orders = [order for order in all_orders if order.is_paid]
        
        payment_methods = {}
        for order in paid_orders:
            method = order.payment_method or 'OTHER'
            payment_methods[method] = payment_methods.get(method, 0) + 1
        
        labels = list(payment_methods.keys())
        data = list(payment_methods.values())
        
        return JsonResponse({
            'labels': labels,
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'labels': ['Error'],
            'data': [0],
            'error': str(e)
        })


@require_GET
def payment_status_chart(request):
    """Get payment status distribution - MongoDB compatible version"""
    try:
        orders = Order.objects.all()
        
        paid_orders = sum(1 for order in orders if order.is_paid)
        unpaid_orders = sum(1 for order in orders if not order.is_paid)
        
        return JsonResponse({
            'labels': ['Paid Orders', 'Unpaid Orders'],
            'data': [paid_orders, unpaid_orders]
        })
    except Exception as e:
        return JsonResponse({
            'labels': ['Error'],
            'data': [0],
            'error': str(e)
        })
