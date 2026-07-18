from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('api/kpi/', views.kpi_data, name='kpi_data'),
    path('api/sales-over-time/', views.sales_over_time, name='sales_over_time'),
    path('api/orders-vs-revenue/', views.orders_vs_revenue, name='orders_vs_revenue'),
    path('api/payment-methods/', views.payment_methods, name='payment_methods'),
    path('api/coupon-usage/', views.coupon_usage, name='coupon_usage'),
    path('api/product-analytics/', views.product_analytics, name='product_analytics'),
    path('export/pdf/', views.export_dashboard_pdf, name='export_pdf'),
    
    # NEW: Real-time auto-refresh API endpoint
    path('api/live-data/', views.dashboard_live_data, name='live_data'),
]
