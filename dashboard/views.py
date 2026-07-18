from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
import json
from store.models import Order, Product, Review, CartItem
from django.contrib.auth import logout
from django.contrib import messages

def get_date_range(filter_type):
    """Utility function to get date range based on filter"""
    now = timezone.now()
    if filter_type == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif filter_type == 'yesterday':
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif filter_type == 'last_7_days':
        start = now - timedelta(days=7)
        end = now
    elif filter_type == 'last_month':
        start = now - timedelta(days=30)
        end = now
    else:
        start = now - timedelta(days=30)
        end = now
    return start, end

def dashboard_home(request):
    """Main dashboard view - serves standalone HTML"""
    from django.http import HttpResponse
    import os
    
    # Get the absolute path to the standalone HTML file
    html_file_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'dashboard_standalone.html')
    
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HttpResponse(html_content)
    except FileNotFoundError:
        return HttpResponse("Dashboard file not found", status=404)

def kpi_data(request):
    """API endpoint for KPI cards"""
    filter_type = request.GET.get('filter', 'last_7_days')
    start_date, end_date = get_date_range(filter_type)
    
    # Get all orders and filter in Python to avoid Djongo issues
    all_orders = list(Order.objects.filter(status='success'))
    
    # Filter orders by date range in Python
    orders_in_range = []
    for order in all_orders:
        if order.created_at and start_date <= order.created_at <= end_date:
            orders_in_range.append(order)
    
    # Total Orders
    total_orders = len(orders_in_range)
    
    # Total Sales (sum of quantities from cart items)
    # Note: Since Order doesn't have quantity, we'll use total_orders as proxy
    total_sales = total_orders
    
    # Total Revenue (handle Decimal128 from MongoDB)
    total_revenue = sum(float(str(order.total_amount)) for order in orders_in_range if order.total_amount)
    
    # Total Coupon Discount (handle Decimal128 from MongoDB)
    total_coupon_discount = sum(float(str(order.discount_amount)) for order in orders_in_range if order.discount_amount)
    
    data = {
        'total_orders': total_orders,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_coupon_discount': total_coupon_discount,
        'filter_type': filter_type
    }
    
    return JsonResponse(data)

def sales_over_time(request):
    """API endpoint for sales over time chart"""
    filter_type = request.GET.get('filter', 'last_7_days')
    start_date, end_date = get_date_range(filter_type)
    
    # Get all orders and filter in Python to avoid Djongo issues
    all_orders = list(Order.objects.filter(status='success'))
    
    # Filter orders by date range in Python
    orders_in_range = []
    for order in all_orders:
        if order.created_at and start_date <= order.created_at <= end_date:
            orders_in_range.append(order)
    
    # Group by date
    if filter_type == 'today':
        # Group by hour for today
        sales_data = []
        for hour in range(24):
            hour_start = start_date.replace(hour=hour, minute=0, second=0)
            hour_end = start_date.replace(hour=hour, minute=59, second=59)
            revenue = sum(float(str(order.total_amount)) for order in orders_in_range 
                         if hour_start <= order.created_at <= hour_end)
            sales_data.append({
                'x': f"{hour:02d}:00",
                'y': float(revenue)
            })
    else:
        # Group by day for other filters
        sales_data = []
        current_date = start_date.date()
        while current_date <= end_date.date():
            day_revenue = sum(float(str(order.total_amount)) for order in orders_in_range 
                            if order.created_at.date() == current_date)
            sales_data.append({
                'x': current_date.strftime('%Y-%m-%d'),
                'y': float(day_revenue)
            })
            current_date += timedelta(days=1)
    
    return JsonResponse({'data': sales_data})

def orders_vs_revenue(request):
    """API endpoint for Bar Chart - Orders vs Revenue"""
    filter_type = request.GET.get('filter', 'last_7_days')
    start_date, end_date = get_date_range(filter_type)
    
    # Get all orders and filter in Python to avoid Djongo issues
    all_orders = list(Order.objects.filter(status='success'))
    
    # Filter orders by date range in Python
    orders_in_range = []
    for order in all_orders:
        if order.created_at and start_date <= order.created_at <= end_date:
            orders_in_range.append(order)
    
    # Group by date
    orders_data = []
    revenue_data = []
    labels = []
    
    current_date = start_date.date()
    while current_date <= end_date.date():
        day_orders = [order for order in orders_in_range if order.created_at.date() == current_date]
        order_count = len(day_orders)
        revenue = sum(float(str(order.total_amount)) for order in day_orders)
        
        labels.append(current_date.strftime('%Y-%m-%d'))
        orders_data.append(order_count)
        revenue_data.append(float(revenue))
        
        current_date += timedelta(days=1)
    
    data = {
        'labels': labels,
        'orders': orders_data,
        'revenue': revenue_data
    }
    
    return JsonResponse(data)

def payment_methods(request):
    """API endpoint for Pie Chart - Payment Methods"""
    filter_type = request.GET.get('filter', 'last_7_days')
    start_date, end_date = get_date_range(filter_type)
    
    # Get all orders and filter in Python to avoid Djongo issues
    all_orders = list(Order.objects.filter(status='success'))
    
    # Filter orders by date range in Python
    orders_in_range = []
    for order in all_orders:
        if order.created_at and start_date <= order.created_at <= end_date:
            orders_in_range.append(order)
    
    # Count by payment method in Python
    payment_counts = {}
    for order in orders_in_range:
        method = order.payment_method or 'Unknown'
        payment_counts[method] = payment_counts.get(method, 0) + 1
    
    data = []
    for method, count in sorted(payment_counts.items(), key=lambda x: x[1], reverse=True):
        method_name = method.title() if method else 'Unknown'
        data.append({
            'label': method_name,
            'value': count
        })
    
    return JsonResponse({'data': data})

def coupon_usage(request):
    """API endpoint for Doughnut Chart - Coupon Usage"""
    filter_type = request.GET.get('filter', 'last_7_days')
    start_date, end_date = get_date_range(filter_type)
    
    # Get all orders and filter in Python to avoid Djongo issues
    all_orders = list(Order.objects.filter(status='success'))
    
    # Filter orders by date range in Python
    orders_in_range = []
    for order in all_orders:
        if order.created_at and start_date <= order.created_at <= end_date:
            orders_in_range.append(order)
    
    # Count orders with and without coupons
    total_orders = len(orders_in_range)
    with_coupon = len([order for order in orders_in_range if order.coupon_code and order.coupon_code.strip()])
    without_coupon = total_orders - with_coupon
    
    data = [
        {'label': 'With Coupon', 'value': with_coupon},
        {'label': 'Without Coupon', 'value': without_coupon}
    ]
    
    return JsonResponse({'data': data})

def product_analytics(request):
    """API endpoint for Product Analytics"""
    filter_type = request.GET.get('filter', 'last_7_days')
    start_date, end_date = get_date_range(filter_type)
    
    # Top 5 Selling Products (by quantity)
    # Since we don't have OrderItem model with quantity, we'll use order frequency
    top_selling = Product.objects.filter(
        order_products__created_at__range=[start_date, end_date],
        order_products__status='success'
    ).annotate(
        order_count=Count('order_products')
    ).order_by('-order_count')[:5]
    
    top_selling_data = []
    for product in top_selling:
        top_selling_data.append({
            'name': product.name,
            'orders': product.order_count
        })
    
    # Top 5 Most Rated Products
    top_rated = Product.objects.annotate(
        avg_rating=Avg('review__rating'),
        review_count=Count('review')
    ).filter(
        review_count__gt=0
    ).order_by('-avg_rating')[:5]
    
    top_rated_data = []
    for product in top_rated:
        top_rated_data.append({
            'name': product.name,
            'rating': round(product.avg_rating, 2) if product.avg_rating else 0,
            'reviews': product.review_count
        })
    
    data = {
        'top_selling': top_selling_data,
        'top_rated': top_rated_data
    }
    
    return JsonResponse(data)

def export_dashboard_pdf(request):
    """Export Dashboard as PDF - Simple version"""
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="dashboard_report.txt"'
    
    content = """
    ANALYTICS DASHBOARD REPORT
    ==========================
    
    This is a placeholder for PDF export.
    In production, this would generate a complete PDF report.
    
    Dashboard Features:
    - Total Orders
    - Total Sales
    - Total Revenue
    - Coupon Discounts
    - Product Analytics
    - Sales Charts
    
    Generated on: {}
    """.format(timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    response.write(content)
    return response


def dashboard_live_data(request):
    """
    API endpoint for real-time dashboard data refresh
    Returns JSON with current KPI metrics
    Used by JavaScript to auto-refresh dashboard every 5-10 seconds
    """
    from django.contrib.auth.decorators import login_required
    
    # Only authenticated users can access this endpoint
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    filter_type = request.GET.get('filter', 'last_7_days')
    start_date, end_date = get_date_range(filter_type)
    
    try:
        # Get orders in the date range with success status
        orders = Order.objects.filter(
            created_at__range=[start_date, end_date],
            status='success'
        )
        
        # Calculate KPI metrics
        total_orders = orders.count()
        total_sales = total_orders
        total_revenue = orders.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # Get paid and unpaid orders
        paid_orders = orders.filter(payment_status='Paid').count()
        unpaid_orders = orders.filter(payment_status='Unpaid').count()
        
        # Get failed orders
        failed_orders = Order.objects.filter(
            created_at__range=[start_date, end_date],
            status='failed'
        ).count()
        
        # Get total coupon discount (0 if not in model)
        total_coupon_discount = 0
        
        # Current timestamp
        import datetime as dt
        current_time = dt.datetime.now().strftime('%H:%M:%S')
        
        data = {
            'total_orders': total_orders,
            'total_sales': total_sales,
            'total_revenue': float(total_revenue),
            'paid_orders': paid_orders,
            'unpaid_orders': unpaid_orders,
            'failed_orders': failed_orders,
            'total_coupon_discount': total_coupon_discount,
            'last_updated': current_time,
            'filter_type': filter_type,
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(data)
    
    except Exception as e:
        return JsonResponse(
            {'error': str(e)}, 
            status=500
        )


def logout_view(request):
    """
    Logout user and redirect to shop page
    """
    try:
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('shop')
    except Exception as e:
        messages.error(request, 'An error occurred during logout.')
        return redirect('shop')
