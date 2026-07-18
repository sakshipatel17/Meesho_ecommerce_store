from django.contrib import admin
from .models import Category,Product,Order,Review,Wishlist,Cart,CartItem,ProductImage,Coupon,CouponUsage

admin.site.register(Category)

class ProductImageInline(admin.TabularInline):
    model = ProductImage

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]

admin.site.register(Product,ProductAdmin)

class OrderAdmin(admin.ModelAdmin):
    """Enhanced Order Admin with order lifecycle management"""
    list_display = ('order_id', 'tracking_id', 'customer_name', 'status', 'total_amount', 'is_paid', 'created_at')
    list_filter = ('status', 'is_paid', 'payment_method', 'created_at')
    search_fields = ('order_id', 'tracking_id', 'customer__email', 'name')
    readonly_fields = ('order_id', 'tracking_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'tracking_id', 'customer', 'status', 'is_paid')
        }),
        ('Order Timeline', {
            'fields': ('created_at', 'updated_at', 'shipped_date', 'delivered_date', 'estimated_delivery')
        }),
        ('Customer Details', {
            'fields': ('name', 'phone', 'address', 'city', 'state', 'pincode')
        }),
        ('Payment Information', {
            'fields': ('total_amount', 'discount_amount', 'coupon_code', 'payment_method', 'payment_id')
        }),
    )
    
    def customer_name(self, obj):
        return obj.customer.email
    customer_name.short_description = 'Customer'

admin.site.register(Order, OrderAdmin)
admin.site.register(Review)
admin.site.register(Wishlist)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Coupon)
admin.site.register(CouponUsage)