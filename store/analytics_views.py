from django.db.models import Sum, Count, Avg, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate, TruncDay, TruncMonth
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta, datetime
from .models import Order, CartItem, Product
from django.views.decorators.http import require_GET
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
    """Get KPI data for analytics dashboard"""
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
    
    total_orders = len(paid_orders_in_range)
    total_sales = len(paid_orders_in_range)
    
    # Calculate revenue from paid orders in date range (handle Decimal128 from MongoDB)
    total_revenue = sum(float(str(order.total_amount)) for order in paid_orders_in_range if order.total_amount)
    
    # Payment methods distribution (from paid orders in date range)
    payment_methods_counts = {}
    for order in paid_orders_in_range:
        method = order.payment_method or 'Other'
        payment_methods_counts[method] = payment_methods_counts.get(method, 0) + 1
    
    payment_methods = [
        {'payment_method': method, 'count': count}
        for method, count in payment_methods_counts.items()
    ]
    
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
        'payment_methods': payment_methods,
        'filter_type': filter_type,
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        }
    }
    
    return JsonResponse(data)


@require_GET
def sales_over_time(request):
    """Get sales data over time for line chart"""
    filter_type = request.GET.get('filter', 'last_7_days')
    
    # Get date range for filtering
    start_date, end_date = get_date_range(filter_type)
    
    # Get all orders and filter in Python to avoid Djongo boolean field issues
    all_orders = list(Order.objects.all())
    paid_orders_in_range = []
    
    # Filter orders by date range and payment status
    for order in all_orders:
        if order.is_paid and order.created_at:
            if start_date <= order.created_at <= end_date:
                paid_orders_in_range.append(order)
    
    # Group by date
    sales_data = {}
    for order in paid_orders_in_range:
        date_key = order.created_at.date()
        if date_key not in sales_data:
            sales_data[date_key] = {'orders_count': 0, 'revenue': 0}
        sales_data[date_key]['orders_count'] += 1
        sales_data[date_key]['revenue'] += float(str(order.total_amount))
    
    # Sort by date
    sorted_dates = sorted(sales_data.keys())
    
    labels = []
    orders_data = []
    revenue_data = []
    
    for date in sorted_dates:
        labels.append(date.strftime('%Y-%m-%d'))
        orders_data.append(sales_data[date]['orders_count'])
        revenue_data.append(sales_data[date]['revenue'])
    
    return JsonResponse({
        'labels': labels,
        'orders': orders_data,
        'revenue': revenue_data
    })


@require_GET
def orders_vs_revenue(request):
    """Get orders vs revenue data for bar chart"""
    filter_type = request.GET.get('filter', 'last_7_days')
    
    # Get date range for filtering
    start_date, end_date = get_date_range(filter_type)
    
    # Get all orders and filter in Python to avoid Djongo boolean field issues
    all_orders = list(Order.objects.all())
    paid_orders_in_range = []
    
    # Filter orders by date range and payment status
    for order in all_orders:
        if order.is_paid and order.created_at:
            if start_date <= order.created_at <= end_date:
                paid_orders_in_range.append(order)
    
    # Group by date
    daily_data = {}
    for order in paid_orders_in_range:
        date_key = order.created_at.date()
        if date_key not in daily_data:
            daily_data[date_key] = {'orders_count': 0, 'revenue_sum': 0}
        daily_data[date_key]['orders_count'] += 1
        daily_data[date_key]['revenue_sum'] += float(str(order.total_amount))
    
    # Sort by date
    sorted_dates = sorted(daily_data.keys())
    
    labels = []
    orders = []
    revenue = []
    
    for date in sorted_dates:
        labels.append(date.strftime('%b %d'))
        orders.append(daily_data[date]['orders_count'])
        revenue.append(daily_data[date]['revenue_sum'])
    
    return JsonResponse({
        'labels': labels,
        'orders': orders,
        'revenue': revenue
    })


@require_GET
def payment_methods_chart(request):
    """Get payment methods distribution for pie chart"""
    filter_type = request.GET.get('filter', 'last_7_days')
    
    # Get date range for filtering
    start_date, end_date = get_date_range(filter_type)
    
    # Get all orders and filter in Python to avoid Djongo boolean field issues
    all_orders = list(Order.objects.all())
    paid_orders_in_range = []
    
    # Filter orders by date range and payment status
    for order in all_orders:
        if order.is_paid and order.created_at:
            if start_date <= order.created_at <= end_date:
                paid_orders_in_range.append(order)
    
    # Count payment methods
    payment_data = {}
    for order in paid_orders_in_range:
        method = order.payment_method or 'Other'
        payment_data[method] = payment_data.get(method, 0) + 1
    
    labels = []
    data = []
    
    for method, count in sorted(payment_data.items(), key=lambda x: x[1], reverse=True):
        method_name = method.upper() if method else 'OTHER'
        labels.append(method_name)
        data.append(count)
    
    return JsonResponse({
        'labels': labels,
        'data': data
    })


@require_GET
def payment_status_chart(request):
    """Get payment status distribution for doughnut chart"""
    filter_type = request.GET.get('filter', 'last_7_days')
    
    # Get date range for filtering
    start_date, end_date = get_date_range(filter_type)
    
    # Get all orders and filter in Python to avoid Djongo boolean field issues
    all_orders = list(Order.objects.all())
    orders_in_range = []
    
    # Filter orders by date range
    for order in all_orders:
        if order.created_at:
            if start_date <= order.created_at <= end_date:
                orders_in_range.append(order)
    
    # Count paid and unpaid orders in date range
    paid_orders = [order for order in orders_in_range if order.is_paid]
    unpaid_orders = [order for order in orders_in_range if not order.is_paid]
    
    return JsonResponse({
        'labels': ['Paid Orders', 'Unpaid Orders'],
        'data': [len(paid_orders), len(unpaid_orders)]
    })