from django.urls import path
from . import views
from . import analytics_views
from . import order_views
from . import chatbot_views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path("",views.shop,name="shop"),
    path("minimal/",views.minimal_shop,name="minimal_shop"),
    path("product/<slug>/",views.product,name="product"),
    path("cart/",views.cart,name="cart"),
    path("add-to-cart/<id>/",views.add_to_cart,name="add_to_cart"),
    path("remove-from-cart/<id>/",views.remove_from_cart,name="remove_from_cart"),
    path("increase-quantity/<id>/",views.increase_quantity,name="increase_quantity"),
    path("decrease-quantity/<id>/",views.decrease_quantity,name="decrease_quantity"),
    path("checkout/",views.checkout,name="checkout"),
    path("payment-success/<id>/",views.payment_success,name="payment_success"),
    path("payment-failed/<id>/",views.payment_failed,name="payment_failed"),
    path("dashboard/",views.user_dashboard,name="dashboard"),
    path("change-password/", auth_views.PasswordChangeView.as_view(
        template_name='store/change_password.html',
        success_url='/dashboard/'
    ), name='change_password'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path("orders/",views.orders,name="orders"),
    path("order-details/",views.order_details,name="order_details"),
    path("wishlist/",views.wishlist,name="wishlist"),
    path("add-to-wishlist/<id>/",views.add_to_wishlist,name="add_to_wishlist"),
    path("wishlist/remove/<uuid:product_id>/", views.remove_from_wishlist, name="remove_from_wishlist"),
    path("wishlist/toggle/<product_id>/",views.toggle_wishlist,name="toggle_wishlist"),
    path("buy-now/<id>/",views.buy_now,name="buy_now"),
    path("rate-product/<id>/", views.rate_product, name="rate_product"),
    path("get-payment-method-ui/", views.get_payment_method_ui, name="get_payment_method_ui"),
    path("apply-coupon/", views.apply_coupon, name="apply_coupon"),
    path("generate-qr-code/", views.generate_qr_code, name="generate_qr_code"),
    
    # New Order Management Routes (Myntra-style lifecycle)
    path("orders/track/<str:order_id>/", order_views.order_tracking, name="order_track"),
    path("orders/<str:order_id>/details/", order_views.order_details, name="order_detail"),
    path("my-orders/", order_views.my_orders, name="my_orders"),
    path("orders/<str:order_id>/cancel/", order_views.cancel_order, name="cancel_order"),
    path("orders/<str:order_id>/resend-email/", order_views.resend_order_email, name="resend_order_email"),
    path("api/orders/<str:order_id>/status/", order_views.update_order_status, name="update_order_status"),
    path("api/orders/<str:order_id>/timeline/", order_views.get_order_timeline_api, name="api_order_timeline"),
    
    # Analytics Routes
    path("analytics/kpis/", analytics_views.analytics_kpis),
    path("analytics/sales/", analytics_views.sales_over_time),
    path("analytics/orders-revenue/", analytics_views.orders_vs_revenue),
    path("analytics/payment-methods/", analytics_views.payment_methods_chart),
    path("analytics/payment-status/", analytics_views.payment_status_chart),
    
    # Chatbot API
    path("api/chatbot/", chatbot_views.chatbot_response, name="chatbot_response"),
    
    # Static Pages
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    
    # Order Actions
    path("cancel-order/<int:order_id>/", views.cancel_order, name='cancel_order'),
    path("return-order/<str:order_id>/", views.return_order, name="return_order"),
    path("mark-shipped/<str:order_id>/", views.mark_order_shipped, name="mark_order_shipped"),
    path("download-invoice/<str:order_id>/", views.download_invoice, name="download_invoice"),
]
