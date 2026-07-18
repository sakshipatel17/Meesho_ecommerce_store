"""
URL configuration for kostaa project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include,re_path
from django.conf import settings
from django.views.static import serve
from store import analytics_simple as analytics_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("",include("store.urls")),
    path("accounts/",include("accounts.urls")),
    path("dashboard/",include("dashboard.urls")),
    path('social/', include('allauth.urls')),
    # Analytics API endpoints
    path('api/analytics/kpis/', analytics_views.analytics_kpis, name='analytics_kpis'),
    path('api/analytics/sales-over-time/', analytics_views.sales_over_time, name='sales_over_time'),
    path('api/analytics/orders-vs-revenue/', analytics_views.orders_vs_revenue, name='orders_vs_revenue'),
    path('api/analytics/payment-methods/', analytics_views.payment_methods_chart, name='payment_methods_chart'),
    path('api/analytics/payment-status/', analytics_views.payment_status_chart, name='payment_status_chart'),
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}), 
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
]
