from django.db import models
import uuid
from shortuuid.django_fields import ShortUUIDField
from accounts.models import User
from django.template.defaultfilters import slugify
from django.core.validators import MaxValueValidator,MinValueValidator
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Product(models.Model):
    id = models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True)
    sno = models.CharField(max_length=255,blank=True,null=True,unique=True)
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="store/products/")
    description = models.TextField()
    price = models.DecimalField(max_digits=8,decimal_places=2)
    category = models.ForeignKey(Category,on_delete=models.CASCADE)
    length = models.DecimalField(max_digits=8,decimal_places=2,default=0)
    weight = models.DecimalField(max_digits=8,decimal_places=2,default=0)
    in_stock = models.IntegerField(default=0)
    slug = models.SlugField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self,*args, **kwargs):
        self.slug = slugify(self.name)
        if not self.sno:
            last_product = Product.objects.order_by('-id').first()
            if last_product:
                last_serial_number = last_product.sno
                last_serial_number = last_serial_number[3:]  # Extract the numeric part
                sno = int(last_serial_number) + 1
            else:
                sno = 1
            self.sno = f'KST{str(sno).zfill(4)}'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="store/products/images")

    def __str__(self):
        return self.product.name

class Order(models.Model):
    # Order Status Choices
    STATUS_CHOICES = (
        ('pending', 'Order Placed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('return_requested', 'Return Requested'),
    )
    
    order_id = ShortUUIDField(
        length=8,
        max_length=40,
        alphabet="0123456789",
        primary_key=True,
    )
    tracking_id = models.CharField(max_length=20, unique=True, blank=True, null=True, help_text="Unique tracking ID for order")
    customer = models.ForeignKey(User,on_delete=models.CASCADE)
    products = models.ManyToManyField(Product,related_name="order_products")
    total_amount = models.DecimalField(max_digits=10,decimal_places=2)
    name = models.CharField(max_length=255, default="")
    address = models.CharField(max_length=255,default="")
    city = models.CharField(max_length=255,default="")
    state = models.CharField(max_length=255,default="")
    pincode = models.CharField(max_length=6,default="")
    phone = models.CharField(max_length=15,blank=True,null=True)
    payment_method = models.CharField(max_length=20, choices=(
        ("cod", "Cash on Delivery"),
        ("card", "Credit/Debit Card"),
        ("upi", "UPI Payment"),
        ("paytm", "Paytm Wallet"),
        ("razorpay", "Razorpay"),
        ("stripe", "Stripe")
    ), default="cod")   
    payment_id = models.CharField(max_length=255,blank=True,null=True)
    status = models.CharField(max_length=50,choices=STATUS_CHOICES,default="pending")
    is_paid = models.BooleanField(default=False)
    
    # Order Lifecycle Timestamps
    shipped_date = models.DateTimeField(blank=True, null=True, help_text="Date when order was dispatched")
    delivered_date = models.DateTimeField(blank=True, null=True, help_text="Date when order was delivered")
    estimated_delivery = models.DateField(blank=True, null=True, help_text="Estimated delivery date")
    
    # NEW FIELDS FOR COUPON & DISCOUNT TRACKING
    coupon_code = models.CharField(max_length=50, blank=True, null=True, help_text="Coupon code applied to this order")
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Total discount amount applied")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.order_id)
    
    def save(self, *args, **kwargs):
        # Ensure total_amount is a proper Decimal
        if self.total_amount is not None:
            try:
                from decimal import Decimal
                if isinstance(self.total_amount, (int, float, str)):
                    self.total_amount = Decimal(str(self.total_amount))
            except (ValueError, TypeError):
                from decimal import Decimal
                self.total_amount = Decimal('0.00')
        
        # Auto-generate tracking ID if not present
        if not self.tracking_id:
            import uuid
            self.tracking_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
class Review(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[
            MaxValueValidator(5),
            MinValueValidator(1)
        ])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review of {self.product.name} by {self.user.email}"

class Wishlist(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    product = models.ManyToManyField(Product,related_name="wishlist_product")

    def __str__(self):
        return f"Wishlist of {self.user.email}"
    
class Cart(models.Model):
    id = models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE)

    def __str__(self):
        return self.user.email

class CartItem(models.Model):
    cart = models.ForeignKey(Cart,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    subtotal = models.FloatField(default=0)  # Changed to FloatField for Djongo compatibility

    def __str__(self):
        return self.product.name
    
    def save(self, *args, **kwargs):
        # Convert Decimal128 from MongoDB to float (djongo compatibility)
        price = float(str(self.product.price))
        self.subtotal = float(self.quantity * price)
        super().save(*args, **kwargs)

class Coupon(models.Model):
    """Coupon model to track all available coupons"""
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )
    
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.FloatField()  # Changed from DecimalField for Djongo compatibility
    
    # Eligibility rules
    min_order_amount = models.FloatField(default=0, help_text="Minimum order amount required to use this coupon")
    max_discount_amount = models.FloatField(null=True, blank=True, help_text="Maximum discount that can be applied")
    
    # Usage restrictions
    is_for_first_order = models.BooleanField(default=False, help_text="This coupon is only for first-time orders")
    usage_limit_per_user = models.IntegerField(default=1, help_text="How many times a user can use this coupon")
    
    # Active/Inactive
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.code

class CouponUsage(models.Model):
    """Track coupon usage per user"""
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='coupon_usage')
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('coupon', 'user', 'order')
    
    def __str__(self):
        return f"{self.coupon.code} used by {self.user.email}"

# AI FEATURE MODELS

class WishlistItem(models.Model):
    """Enhanced wishlist item with tracking and AI features"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    last_notified = models.DateTimeField(null=True, blank=True, help_text="Last time user was notified about this item")
    notification_count = models.IntegerField(default=0, help_text="Number of notifications sent")
    is_active = models.BooleanField(default=True, help_text="Whether this item is still in wishlist")
    
    class Meta:
        unique_together = ('user', 'product')
    
    def __str__(self):
        return f"{self.user.email} - {self.product.name}"

class UserBehavior(models.Model):
    """Track user behavior for AI recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=20, choices=(
        ('view', 'Viewed'),
        ('wishlist', 'Added to Wishlist'),
        ('cart', 'Added to Cart'),
        ('purchase', 'Purchased'),
        ('search', 'Searched'),
    ))
    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.action_type} - {self.product.name}"

class AIRecommendation(models.Model):
    """AI-generated product recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    recommendation_type = models.CharField(max_length=20, choices=(
        ('similar', 'Similar Items'),
        ('trending', 'Trending Products'),
        ('personalized', 'Personalized'),
        ('frequently_bought', 'Frequently Bought Together'),
    ))
    score = models.FloatField(default=0.0, help_text="AI confidence score")
    created_at = models.DateTimeField(auto_now_add=True)
    is_clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Recommendation for {self.user.email} - {self.product.name}"

class SmartOffer(models.Model):
    """AI-generated smart offers based on user behavior"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    offer_type = models.CharField(max_length=20, choices=(
        ('discount', 'Special Discount'),
        ('flash_sale', 'Flash Sale'),
        ('bundle', 'Bundle Offer'),
        ('loyalty', 'Loyalty Reward'),
    ))
    discount_percentage = models.FloatField(default=0.0)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    trigger_reason = models.CharField(max_length=255, help_text="Why this offer was triggered")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.offer_type} for {self.user.email}"

class SellerRating(models.Model):
    """Enhanced seller rating for fake seller detection"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MaxValueValidator(5), MinValueValidator(1)])
    is_verified_purchase = models.BooleanField(default=False)
    review_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Rating by {self.user.email} for {self.product.name}"

class SellerTrustScore(models.Model):
    """AI-calculated seller trust score"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trust_score = models.FloatField(default=0.0, help_text="Trust score from 0 to 100")
    total_ratings = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    return_rate = models.FloatField(default=0.0, help_text="Percentage of returns")
    fake_review_probability = models.FloatField(default=0.0, help_text="AI-detected fake review probability")
    is_verified = models.BooleanField(default=False)
    last_calculated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Trust Score for {self.user.email}: {self.trust_score}"

class VoiceSearch(models.Model):
    """Track voice search queries"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    query_text = models.TextField(help_text="Converted speech to text")
    original_audio = models.FileField(upload_to="voice_search/", null=True, blank=True)
    search_results_count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"Voice Search: {self.query_text[:50]}..."

class VirtualTryOn(models.Model):
    """Virtual try-on sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user_image = models.ImageField(upload_to="virtual_tryon/user_images/")
    result_image = models.ImageField(upload_to="virtual_tryon/results/", null=True, blank=True)
    try_on_type = models.CharField(max_length=20, choices=(
        ('clothing', 'Clothing'),
        ('jewelry', 'Jewelry'),
        ('makeup', 'Makeup'),
    ))
    created_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Virtual Try-On: {self.user.email} - {self.product.name}"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Contact Message from {self.name} - {self.email}"
    
    class Meta:
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"