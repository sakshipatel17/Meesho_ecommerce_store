from django.shortcuts import render,redirect,get_object_or_404
from .models import Product,Order,Review,Wishlist,Cart,CartItem,ProductImage,Category,Coupon,CouponUsage,ContactMessage
from django.contrib.auth.decorators import login_required
from django.db.models import Q,Avg,Count
from django.contrib import messages
from django.core.paginator import Paginator
import uuid
from django.http import JsonResponse, HttpResponse
from decouple import config
from django.db.models import Q,Avg
from .helper import sendOrderEmail, is_first_time_buyer, can_use_coupon, calculate_discount, get_eligible_coupons_for_user, track_coupon_usage
from .payment_helper import generate_upi_qr_code, generate_paytm_qr_code, validate_card, validate_upi_id
from decimal import Decimal
import stripe
from .forms import UserUpdateForm
from .email_utils import send_order_email, send_order_html_email
from .simple_email import send_order_email as send_simple_order_email
from .order_email_utils import send_order_notification
from .cart_helper import get_or_create_cart, add_to_session_cart, remove_from_session_cart, get_session_cart_items, debug_cart_state
from django.http import HttpResponse
from decimal import Decimal




# Initialize Stripe with error handling
try:
    stripe.api_key=config("STRIPE_API_KEY")
    STRIPE_ENABLED = True
except:
    stripe.api_key = None
    STRIPE_ENABLED = False

def minimal_shop(request):
    search = request.GET.get('search', None)
    if search:
        products = Product.objects.filter(name__icontains=search)
    else:
        products = Product.objects.prefetch_related('productimage_set').all()
    return render(request, 'store/minimal_shop.html',{'products':products})

def shop(request):
    search = request.GET.get('search', None)
    category_id = request.GET.get('category', None)
    
    # Get all categories
    categories = Category.objects.all()
    
    # Filter products
    products = Product.objects.prefetch_related('productimage_set').all()
    
    if search:
        # Split search into tokens and require each token to match name, description or category name.
        # Build a single Q object with AND-ed token clauses to avoid multiple chained filters (better DB compatibility).
        try:
            tokens = [t.strip() for t in search.split() if t.strip()]
            combined_q = None
            for token in tokens:
                q_token = Q(name__icontains=token) | Q(description__icontains=token) | Q(category__name__icontains=token)
                combined_q = q_token if combined_q is None else (combined_q & q_token)
            if combined_q is not None:
                # Attempt to apply the combined Q. Force a small DB call (.exists()) so
                # any DB-side errors (e.g., djongo iLIKE issues) surface here and are
                # caught by the outer try/except instead of during template rendering.
                candidate = products.filter(combined_q)
                # force execution
                _ = candidate.exists()
                products = candidate
        except Exception:
            # If the DB (djongo) cannot handle complex queries (e.g., iLIKE not supported),
            # fall back to loading the candidate products and performing a case-insensitive
            # token-match in Python. This avoids generating unsupported SQL operators.
            try:
                prod_list = list(products)
                lowered_tokens = [t.lower() for t in tokens]
                def matches(p):
                    hay = ' '.join([
                        (p.name or ''),
                        (p.description or ''),
                        (p.category.name or '')
                    ]).lower()
                    return all(tok in hay for tok in lowered_tokens)
                products = [p for p in prod_list if matches(p)]
            except Exception:
                # As a last resort, return all products (prevent crash)
                products = list(Product.objects.all())
    
    if category_id:
        try:
            category = Category.objects.get(id=category_id)
            products = products.filter(category=category)
            selected_category = category
        except Category.DoesNotExist:
            selected_category = None
    else:
        selected_category = None
    
    # Apply sorting
    sort_option = request.GET.get('sort', '')
    
    if sort_option == 'price_asc':
        products = products.order_by('price')
    elif sort_option == 'price_desc':
        products = products.order_by('-price')
    elif sort_option == 'newest':
        products = products.order_by('-created_at')
    else:  # relevance or default
        # Keep default order (no additional sorting)
        pass
    
    total_products = Product.objects.count()
    
    # Check wishlist status for logged-in users
    wishlist_products = []
    wishlist_ids = []
    if request.user.is_authenticated:
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            wishlist_products = wishlist.product.all()
            wishlist_ids = [product.id for product in wishlist_products]
        except Wishlist.DoesNotExist:
            wishlist_products = []
            wishlist_ids = []
    
    return render(request, 'store/shop.html', {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'total_products': total_products,
        'wishlist_products': wishlist_products,
        'wishlist_ids': wishlist_ids
    })

def product(request,slug):
    product = get_object_or_404(Product,slug=slug)
    
    # Check if product is in user's wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            in_wishlist = product in wishlist.product.all()
        except Wishlist.DoesNotExist:
            in_wishlist = False
        except Exception as e:
            print(f"Error checking wishlist: {e}")
            in_wishlist = False
    
    try:
        review = Review.objects.filter(product=product)
        rating = review.aggregate(Avg('rating'))['rating__avg']
    except:
        review=None
        rating=None
    related_products = Product.objects.exclude(id=product.id)
    product_images = ProductImage.objects.filter(product=product)
    return render(request, 'store/product.html',{'product':product,'in_wishlist':in_wishlist,'review':review,'related_products':related_products,'product_images':product_images,'rating':rating})

def cart(request):
    print("🛒 CART VIEW CALLED")
    debug_cart_state(request.user, request.session)
    
    if request.user.is_authenticated:
        # Get or create cart (will merge session cart if exists)
        cart = get_or_create_cart(request.user, request.session)
        cart_items = CartItem.objects.filter(cart=cart)
        total_price = sum(float(str(item.subtotal)) if hasattr(item.subtotal, 'to_decimal') else float(item.subtotal) for item in cart_items)
        
        print(f"✅ User cart loaded: {cart_items.count()} items, total: ₹{total_price}")
        return render(request, 'store/cart.html',{'cart_items':cart_items,'total_price':total_price})
    else:
        # For anonymous users, show session cart
        session_items = get_session_cart_items(request.session)
        total_price = sum(item['subtotal'] for item in session_items)
        
        print(f"👤 Session cart loaded: {len(session_items)} items, total: ₹{total_price}")
        return render(request, 'store/cart.html',{'cart_items':session_items,'total_price':total_price,'session_cart':True})

def buy_now(request, id):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            cart = Cart.objects.create(user=request.user)
        
        product = get_object_or_404(Product, pk=id)
        
        # Manual get/create pattern to avoid djongo issues with UUID FK in get_or_create
        try:
            cart_item = CartItem.objects.get(cart=cart, product=product)
            cart_item.quantity += 1
            cart_item.save()
        except CartItem.DoesNotExist:
            cart_item = CartItem(cart=cart, product=product, quantity=1)
            cart_item.save()
            
        return redirect("cart")
    else:
        return redirect("login")

def add_to_cart(request,id):
    print(f"🛒 ADD TO CART CALLED for product {id}")
    debug_cart_state(request.user, request.session)
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart_count = 0
        
        if request.user.is_authenticated:
            # Get or create cart (will merge session cart if exists)
            cart = get_or_create_cart(request.user, request.session)
            product = Product.objects.get(pk=id)
            
            # Get or create cart item
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': 1}
            )
            
            if not created:
                cart_item.quantity += 1
            
            # Ensure subtotal is float before save
            cart_item.subtotal = float(cart_item.quantity * float(str(product.price)))
            cart_item.save()
            
            # Get updated cart count
            cart_count = CartItem.objects.filter(cart__user=request.user).count()
            print(f"✅ Added to authenticated user cart: {product.name}")
        else:
            # Add to session cart for anonymous users
            add_to_session_cart(id, request.session, 1)
            cart = request.session.get('cart', [])
            cart_count = len(cart) if isinstance(cart, list) else 0
            print(f"✅ Added to session cart: product {id}")
        
        return JsonResponse({
            "success": True, 
            "message": "Product added to cart successfully",
            "cart_count": cart_count
        })
    
    # Handle regular form submissions (redirect to cart)
    if request.user.is_authenticated:
        # Get or create cart (will merge session cart if exists)
        cart = get_or_create_cart(request.user, request.session)
        product = Product.objects.get(pk=id)
        
        # Get or create cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
        
        # Ensure subtotal is float before save
        cart_item.subtotal = float(cart_item.quantity * float(str(product.price)))
        cart_item.save()
        
        print(f"✅ Added to authenticated user cart: {product.name}")
        return redirect("cart")
    else:
        # Add to session cart for anonymous users
        add_to_session_cart(id, request.session, 1)
        print(f"✅ Added to session cart: product {id}")
        return redirect("cart")

def remove_from_cart(request,id):
    try:
        cart = Cart.objects.get(user=request.user)
        product = Product.objects.get(pk=id)
        try:
            cart_item = CartItem.objects.get(cart=cart,product=product)
            cart_item.delete()
        except CartItem.DoesNotExist:
            print(f"Cart item not found for product {id}")
    except (Cart.DoesNotExist, Product.DoesNotExist) as e:
        print(f"Error removing from cart: {e}")
    return redirect("cart")

def increase_quantity(request,id):
    try:
        cart = Cart.objects.get(user=request.user)
        product = Product.objects.get(pk=id)
        try:
            cart_item = CartItem.objects.get(cart=cart,product=product)
            cart_item.quantity = int(cart_item.quantity) + 1  # Ensure quantity is an integer
            cart_item.save()
        except CartItem.DoesNotExist:
            print(f"Cart item not found for product {id}")
    except (Cart.DoesNotExist, Product.DoesNotExist) as e:
        print(f"Error increasing quantity: {e}")
    return redirect("cart")

def decrease_quantity(request,id):
    try:
        cart = Cart.objects.get(user=request.user)
        product = Product.objects.get(pk=id)
        try:
            cart_item = CartItem.objects.get(cart=cart,product=product)
            if cart_item.quantity > 1:  # Prevent quantity from going below 1
                cart_item.quantity = int(cart_item.quantity) - 1  # Ensure quantity is an integer
                cart_item.save()
        except CartItem.DoesNotExist:
            print(f"Cart item not found for product {id}")
    except (Cart.DoesNotExist, Product.DoesNotExist) as e:
        print(f"Error decreasing quantity: {e}")
    return redirect("cart")

def checkout(request):
    print("🔍 CHECKOUT VIEW CALLED")
    debug_cart_state(request.user, request.session)
    
    if request.user.is_authenticated:
        user = request.user
        print(f"✅ User authenticated: {user.email}")
        
        # Get or create cart (will merge session cart if exists)
        cart = get_or_create_cart(user, request.session)
        cart_items = CartItem.objects.filter(cart=cart)
        
        if not cart_items:
            print("❌ No cart items found, redirecting to cart")
            return redirect("cart")
        
        print(f"🛒 Cart loaded: {cart_items.count()} items")
        
        # Convert Decimal128 to float before summing
        total_amount = sum(float(str(item.subtotal)) if hasattr(item.subtotal, 'to_decimal') else float(item.subtotal) 
                         for item in cart_items)
        products = [item.product.id for item in cart_items]
        
        print(f"💰 Total amount calculated: ₹{total_amount}")
        
        # Calculate shipping charges based on cart items
        shipping_charges = 0
        for item in cart_items:
            product_price = float(str(item.product.price)) if hasattr(item.product.price, 'to_decimal') else float(item.product.price)
            
            if product_price < 500:
                shipping_charges += 40
            elif product_price < 1000:
                shipping_charges += 60
            elif product_price < 2000:
                shipping_charges += 80
            else:
                shipping_charges += 100
        
        print(f"🚚 Shipping charges: ₹{shipping_charges}")
        
        # Initialize coupon variables
        discount_amount = 0
        coupon_message = ""
        coupon_success = False
        applied_coupon = None
        is_first_order = False
        
        # Check if user is a first-time buyer
        is_first_order = is_first_time_buyer(user)
        print(f"🆕 First time buyer: {is_first_order}")
        
        # Get eligible coupons for this user
        eligible_coupons = get_eligible_coupons_for_user(user, float(total_amount))
        print(f"🎫 Eligible coupons: {len(eligible_coupons)}")
        
        # For first-time buyers, auto-show the first order coupon
        if is_first_order:
            coupon_message = "As a first-time customer, you're eligible for special discounts!"
            coupon_success = False
        
        # Handle AJAX coupon validation request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == "POST":
            print("🎫 AJAX coupon validation request")
            coupon_code = request.POST.get('coupon_code', '').strip().upper()
            
            # Validate coupon eligibility
            is_eligible, eligibility_message = can_use_coupon(user, coupon_code, float(total_amount))
            
            if is_eligible:
                discount_amount, _ = calculate_discount(coupon_code, float(total_amount))
                discount_amount = float(discount_amount)
                coupon_message = f"Coupon '{coupon_code}' applied successfully! Saving ₹{discount_amount:.2f}"
                coupon_success = True
                applied_coupon = coupon_code
                print(f"✅ Coupon applied: {coupon_code}, discount: ₹{discount_amount}")
            else:
                discount_amount = 0
                coupon_message = eligibility_message
                coupon_success = False
                applied_coupon = None
                print(f"❌ Coupon invalid: {eligibility_message}")
            
            # Calculate final total with shipping
            final_total = total_amount + shipping_charges - discount_amount
            
            return JsonResponse({
                'success': coupon_success,
                'message': coupon_message,
                'discount_amount': discount_amount,
                'final_total': final_total,
                'applied_coupon': applied_coupon
            })
        
        # Handle regular checkout form submission
        if request.method == "POST":
            print("📝 POST checkout form submission")
            name = request.POST.get('name')
            address = request.POST.get('address')
            city = request.POST.get('city')
            state = request.POST.get('state')
            pin = request.POST.get('pin')
            phone = request.POST.get('phone')
            payment_method = request.POST.get('pay-method')
            payment_subtype = request.POST.get('online-payment-type', '')
            coupon_code = request.POST.get('coupon-code', '').strip().upper()
            
            print(f"📋 Order details: {name}, {payment_method}")
            
            # If online payment, use the selected payment type
            if payment_method == 'online' and payment_subtype:
                payment_method = payment_subtype
            
            # Validate payment method specific fields
            if payment_method == 'card':
                card_holder = request.POST.get('card-holder', '')
                card_number = request.POST.get('card-number', '').replace(' ', '')
                card_expiry = request.POST.get('card-expiry', '')
                card_cvv = request.POST.get('card-cvv', '')
                
                # Validate card details
                is_valid, error_message = validate_card(card_number, card_expiry, card_cvv)
                if not is_valid:
                    messages.error(request, f'Card validation failed: {error_message}')
                    return redirect('checkout')
                    
            elif payment_method == 'upi':
                upi_id = request.POST.get('upi_id', '')
                is_valid, error_message = validate_upi_id(upi_id)
                if not is_valid:
                    messages.error(request, f'UPI validation failed: {error_message}')
                    return redirect('checkout')
                    
            elif payment_method == 'paytm':
                paytm_phone = request.POST.get('paytm_phone', '')
                if not paytm_phone or len(paytm_phone) != 10 or not paytm_phone.isdigit():
                    messages.error(request, 'Please enter a valid 10-digit Paytm number')
                    return redirect('checkout')
            
            # Apply and validate coupon if provided
            discount_amount = 0
            applied_coupon = None
            
            if coupon_code:
                is_eligible, eligibility_message = can_use_coupon(user, coupon_code, float(total_amount))
                
                if is_eligible:
                    discount_amount, _ = calculate_discount(coupon_code, float(total_amount))
                    discount_amount = float(discount_amount)
                    applied_coupon = coupon_code
                    print(f"✅ Coupon applied in order: {coupon_code}")
            
            # Calculate final total with shipping
            final_total = total_amount + shipping_charges - discount_amount
            print(f"💰 Final total: ₹{final_total}")
            
            # Create order with coupon tracking
            order = Order.objects.create(
                customer=user,
                total_amount=Decimal(str(final_total)),
                name=name,
                address=address,
                city=city,
                state=state,
                pincode=pin,
                phone=phone,
                payment_method=payment_method,
                is_paid=True,
                status='processing',
                coupon_code=applied_coupon,
                discount_amount=Decimal(str(discount_amount))
            )
            order.products.add(*products)
            order.total_amount = Decimal(order.total_amount)
            order.save()
            
            print(f"📦 Order created successfully: {order.order_id}, tracking_id: {order.tracking_id}")
            
            # Email will be sent automatically by signals.py
            print(f"� Email notification triggered for order {order.order_id}")
            
            # Track coupon usage if a coupon was applied
            if applied_coupon:
                track_coupon_usage(user, applied_coupon, order)
                print(f"🎫 Coupon usage tracked: {applied_coupon}")
            
            # Clear cart
            cart_items.delete()
            print("🗑️ Cart cleared after order creation")
            
            # Show order confirmation page
            return render(request, 'store/order_confirmation.html', {
                'order': order,
                'is_first_order': is_first_order,
                'discount_applied': discount_amount > 0
            })
        
        # Calculate initial final total with shipping
        final_total = total_amount + shipping_charges - discount_amount
        
        # Prepare context for template
        context = {
            'cart_items': cart_items,
            'total_amount': total_amount,
            'shipping_charges': shipping_charges,
            'discount_amount': discount_amount,
            'final_total': final_total,
            'coupon_message': coupon_message,
            'coupon_success': coupon_success,
            'is_first_order': is_first_order,
            'eligible_coupons': eligible_coupons
        }
        
        print(f"📄 Rendering checkout template with {len(cart_items)} items")
        return render(request, 'store/checkout.html', context)
    else:
        print("❌ User not authenticated, redirecting to login")
        return redirect("login")

def generate_qr_code(request):
    """
    AJAX endpoint to generate QR codes dynamically
    """
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == "POST":
        payment_type = request.POST.get('payment_type', 'upi')
        amount = request.POST.get('amount', '0')
        
        try:
            amount = float(amount)
            if payment_type == 'upi':
                qr_data = generate_upi_qr_code(amount)
                merchant_id = "store@exampleupi"
            elif payment_type == 'paytm':
                qr_data = generate_paytm_qr_code(amount)
                merchant_id = "9876543210@paytm"
            else:
                return JsonResponse({'success': False, 'message': 'Invalid payment type'})
            
            return JsonResponse({
                'success': True,
                'qr_code': qr_data,
                'merchant_id': merchant_id,
                'amount': amount
            })
        except Exception as e:
            print(f"Error generating QR code: {str(e)}")
            return JsonResponse({'success': False, 'message': 'Failed to generate QR code'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def payment_success(request, id):
    print(f"💳 PAYMENT SUCCESS CALLED for order {id}")
    
    if request.user.is_authenticated:
        user = request.user
        print(f"✅ User authenticated: {user.email}")
        
        try:
            cart = Cart.objects.get(user=user)
            cart_items = CartItem.objects.filter(cart=cart)
            print(f"🛒 Found cart with {cart_items.count()} items")
        except Cart.DoesNotExist:
            cart_items = []
            print("🛒 No cart found")
            
        order = get_object_or_404(Order, order_id=id)
        print(f"📦 Order found: {order.order_id}, tracking_id: {order.tracking_id}")
        
        # Mark order as paid if not already
        if not order.is_paid:
            order.is_paid = True
            order.status = "processing"
            order.save()
            print(f"✅ Order marked as paid and processing")
        else:
            print("ℹ️ Order already marked as paid")
            
        # Prepare and send email
        try:
            context = {
                'cart_items': cart_items,
                'id': str(order.order_id),
                'email': order.customer.email,
                'address': f"{order.address}, {order.city}, {order.state}, {order.pincode}",
                'method': str(order.payment_method).upper(),
                'total': sum(float(item.subtotal) for item in cart_items) if cart_items else order.total_amount,
                'date': order.created_at
            }
            sendOrderEmail(context)
            print(f"📧 Email sent successfully for order {order.order_id}")
        except Exception as e:
            print(f"❌ Error sending email: {e}")
        
        # Clear cart items after successful order
        if cart_items:
            cart_items.delete()
            print("🗑️ Cart cleared after payment success")
                
        print(f"📄 Rendering payment success template for order {order.order_id}")
        return render(request, 'store/payment_success.html', {'order': order})
    else:
        print("❌ User not authenticated, redirecting to login")
        return redirect("login")

@login_required
def rate_product(request, id):
    if request.method == "POST":
        product = get_object_or_404(Product, pk=id)
        rating_val = request.POST.get('rating')
        
        if rating_val:
            try:
                rating_val = int(rating_val)
                if 1 <= rating_val <= 5:
                    # Update or create rating
                    review, created = Review.objects.update_or_create(
                        product=product,
                        user=request.user,
                        defaults={'rating': rating_val}
                    )
                    
                    # Calculate new average and count
                    avg_rating = Review.objects.filter(product=product).aggregate(Avg('rating'))['rating__avg'] or 0
                    total_ratings = Review.objects.filter(product=product).count()
                    
                    return JsonResponse({
                        'success': True,
                        'avg_rating': round(float(avg_rating), 1),
                        'total_ratings': total_ratings,
                        'message': 'Rating submitted successfully!'
                    })
            except (ValueError, TypeError):
                pass
                
        return JsonResponse({'success': False, 'message': 'Invalid rating value'}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

def payment_failed(request,id):
    if request.user.is_authenticated:
        user = request.user
        cart = Cart.objects.get(user=user)
        cart_items = CartItem.objects.filter(cart=cart)
        order = get_object_or_404(Order, order_id=id)
        if order.is_paid:
            return redirect("shop")
        order.status = "failed"
        order.save()
        cart_items.delete()
        return render(request,'store/payment_failed.html')
    return redirect("login")

def user_dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")
    
    # Get user's orders
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    
    # Get user's wishlist products with related products list
    wishlist_products_with_related = []
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        wishlist_products = wishlist.product.all()
        
        # For each wishlist product, check if out of stock and fetch related products
        for product in wishlist_products:
            product_data = {'product': product, 'related': []}
            if product.in_stock == 0:
                # Fetch related products from same category
                related_products = Product.objects.filter(
                    category=product.category
                ).exclude(id=product.id).filter(in_stock__gt=0)[:4]
                product_data['related'] = list(related_products)
            wishlist_products_with_related.append(product_data)
    except Wishlist.DoesNotExist:
        wishlist_products_with_related = []
    
    # Dashboard Tab Selection
    active_tab = request.GET.get('tab', 'profile')
    
    return render(request, 'store/dashboard.html', {
        'orders': orders,
        'wishlist_products_with_related': wishlist_products_with_related,
        'active_tab': active_tab
    })

def order_details(request):
    if not request.user.is_authenticated:
        return redirect("login")
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'accounts/order_details.html', {'orders': orders})

def orders(request):
    """Display user's order history"""
    user_orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'accounts/order_details.html', {'orders': user_orders})

@login_required
def wishlist(request):
    """Display user's wishlist"""
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        wishlist_items = wishlist.product.all()
    except Wishlist.DoesNotExist:
        wishlist_items = []
    
    return render(request, 'accounts/wishlist.html', {'wishlist_items': wishlist_items})

def add_to_wishlist(request,id):
    if not request.user.is_authenticated:
        return redirect("login")
    
    try:
        product = Product.objects.get(pk=id)
        user = request.user
        
        # Get or create user's wishlist
        try:
            wishlist = Wishlist.objects.get(user=user)
        except Wishlist.DoesNotExist:
            wishlist = Wishlist.objects.create(user=user)
        
        # Toggle product in wishlist
        if product in wishlist.product.all():
            wishlist.product.remove(product)
        else:
            wishlist.product.add(product)
    except Product.DoesNotExist:
        pass
    except Exception as e:
        print(f"Error managing wishlist: {e}")
    
    return redirect(request.META.get('HTTP_REFERER', 'shop'))

def remove_from_wishlist(request, id):
    """Remove product from wishlist"""
    if not request.user.is_authenticated:
        return redirect("login")
    
    try:
        product = Product.objects.get(pk=id)
        wishlist = Wishlist.objects.get(user=request.user)
        wishlist.product.remove(product)
    except (Product.DoesNotExist, Wishlist.DoesNotExist):
        pass
    
    return redirect('wishlist')

def toggle_wishlist(request, product_id):
    """AJAX toggle wishlist functionality"""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Login required'})
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})
    
    try:
        product = Product.objects.get(pk=product_id)
        
        # Get or create user's wishlist
        try:
            wishlist = Wishlist.objects.get(user=request.user)
        except Wishlist.DoesNotExist:
            wishlist = Wishlist.objects.create(user=request.user)
        
        if product in wishlist.product.all():
            # Remove from wishlist
            wishlist.product.remove(product)
            return JsonResponse({'status': 'removed'})
        else:
            # Add to wishlist
            wishlist.product.add(product)
            return JsonResponse({'status': 'added'})
            
    except Product.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Product not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'Something went wrong'})


@login_required
def get_payment_method_ui(request):
    """
    AJAX endpoint to get dynamic payment method UI based on payment type
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    payment_type = request.POST.get('payment_type', '').strip()
    total_amount = request.POST.get('total_amount', '0')
    
    try:
        total_amount = float(total_amount)
    except ValueError:
        return JsonResponse({'error': 'Invalid amount'}, status=400)
    
    # Return appropriate HTML based on payment type
    if payment_type == 'card':
        html = f"""
            <div class="mt-4 p-4 bg-blue-50 rounded-lg">
                <h4 class="text-sm font-semibold text-gray-900 mb-4">
                    <i class="fas fa-credit-card text-blue-600"></i>
                    Card Payment Details
                </h4>
                
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Cardholder Name
                        </label>
                        <input 
                            type="text" 
                            id="card-holder"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="John Doe"
                            required
                        />
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Card Number
                        </label>
                        <input 
                            type="text" 
                            id="card-number"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="1234 5678 9012 3456"
                            maxlength="19"
                            required
                        />
                        <small class="text-gray-500">Format: xxxx xxxx xxxx xxxx</small>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">
                                Expiry Date
                            </label>
                            <input 
                                type="text" 
                                id="card-expiry"
                                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="MM/YY"
                                maxlength="5"
                                required
                            />
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">
                                CVV
                            </label>
                            <input 
                                type="text" 
                                id="card-cvv"
                                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="123"
                                maxlength="4"
                                required
                            />
                        </div>
                    </div>
                    
                    <div class="mt-4 p-3 bg-blue-100 rounded-md">
                        <p class="text-xs text-blue-900">
                            <i class="fas fa-info-circle"></i>
                            For demo purposes, use any valid 16-digit number
                        </p>
                    </div>
                </div>
            </div>
        """
        
    elif payment_type == 'upi':
        # Generate UPI QR code
        qr_code = generate_upi_qr_code(total_amount, "store@upi")
        
        html = f"""
            <div class="mt-4 p-4 bg-green-50 rounded-lg">
                <h4 class="text-sm font-semibold text-gray-900 mb-4">
                    <i class="fas fa-mobile-alt text-green-600"></i>
                    UPI Payment
                </h4>
                
                <div class="space-y-4">
                    <div class="bg-white p-4 rounded-md border-2 border-green-200">
                        <p class="text-xs text-gray-600 mb-3">Scan with any UPI app to pay</p>
                        <img 
                            src="/static/images/qrcode.jpeg" 
                            alt="UPI QR Code" 
                            class="w-48 h-48 mx-auto rounded-lg shadow-sm"
                        />
                    </div>
                    
                    <div class="bg-white p-3 rounded-md">
                        <p class="text-sm text-gray-700">
                            <strong>Amount to Pay:</strong> ₹{total_amount:.2f}
                        </p>
                        <p class="text-sm text-gray-600 mt-2">
                            <i class="fas fa-shield-alt text-green-600"></i>
                            Secure payment via UPI
                        </p>
                    </div>
                    
                    <div class="mt-2">
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Or enter UPI ID manually:
                        </label>
                        <input 
                            type="text" 
                            id="upi-id"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                            placeholder="username@bankname"
                        />
                    </div>
                </div>
            </div>
        """
        
    elif payment_type == 'paytm':
        # Generate Paytm QR code
        qr_code = generate_paytm_qr_code(total_amount, "9876543210@paytm")
        
        html = f"""
            <div class="mt-4 p-4 bg-yellow-50 rounded-lg">
                <h4 class="text-sm font-semibold text-gray-900 mb-4">
                    <i class="fas fa-wallet text-yellow-600"></i>
                    Paytm Wallet Payment
                </h4>
                
                <div class="space-y-4">
                    <div class="bg-white p-4 rounded-md border-2 border-yellow-200">
                        <p class="text-xs text-gray-600 mb-3">Scan with Paytm app to pay</p>
                        <img 
                            src="/static/images/qrcode.jpeg" 
                            alt="Paytm QR Code" 
                            class="w-48 h-48 mx-auto rounded-lg shadow-sm"
                        />
                    </div>
                    
                    <div class="bg-white p-3 rounded-md">
                        <p class="text-sm text-gray-700">
                            <strong>Payee:</strong> Kostaa Store
                        </p>
                        <p class="text-sm text-gray-700">
                            <strong>Amount:</strong> ₹{total_amount:.2f}
                        </p>
                        <p class="text-sm text-gray-600 mt-2">
                            <i class="fas fa-check-circle text-yellow-600"></i>
                            Fast and secure payment
                        </p>
                    </div>
                    
                    <div class="mt-2">
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Paytm Phone Number:
                        </label>
                        <input 
                            type="tel" 
                            id="paytm-phone"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                            placeholder="10-digit phone number"
                            maxlength="10"
                        />
                    </div>
                </div>
            </div>
        """
        
    else:
        return JsonResponse({'error': 'Invalid payment type'}, status=400)
    
    return JsonResponse({
        'success': True,
        'html': html,
        'payment_type': payment_type
    })

@login_required
def remove_from_wishlist(request, product_id):
    """Remove product from wishlist via AJAX"""
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id)
            wishlist = Wishlist.objects.get(user=request.user)
            wishlist.product.remove(product)
            
            return JsonResponse({
                'success': True,
                'message': 'Product removed from wishlist'
            })
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product not found'
            })
        except Wishlist.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Wishlist not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error removing product'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request'
    })

@login_required
def edit_profile(request):
    user = request.user
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = UserUpdateForm(instance=user)
    
    return render(request, 'store/edit_profile.html', {'form': form})

def about(request):
    """About Us page"""
    return render(request, 'about.html')

def contact(request):
    """Contact Support page"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        if name and email and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                message=message
            )
            messages.success(request, 'Your message has been sent successfully!')
            return render(request, 'contact.html', {'success': True})
        else:
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'contact.html', {'error': True})
    
    return render(request, 'contact.html')

@login_required
def apply_coupon(request):
    """Handle coupon application via AJAX or form submission"""
    if request.method == "POST":
        coupon_code = request.POST.get('coupon', '').strip().upper()
        
        # Get user's cart and calculate total
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = CartItem.objects.filter(cart=cart)
            if not cart_items:
                return JsonResponse({
                    'success': False,
                    'message': 'Your cart is empty. Add items before applying coupon.'
                })
        except Cart.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Your cart is empty. Add items before applying coupon.'
            })
        
        # Calculate total amount
        total_amount = sum(float(str(item.subtotal)) if hasattr(item.subtotal, 'to_decimal') else float(item.subtotal) 
                         for item in cart_items)
        
        # Calculate shipping charges
        shipping_charges = 0
        for item in cart_items:
            product_price = float(str(item.product.price)) if hasattr(item.product.price, 'to_decimal') else float(item.product.price)
            if product_price < 500:
                shipping_charges += 40
            elif product_price < 1000:
                shipping_charges += 60
            elif product_price < 2000:
                shipping_charges += 80
            else:
                shipping_charges += 100
        
        # Validate coupon eligibility
        is_eligible, eligibility_message = can_use_coupon(request.user, coupon_code, float(total_amount))
        
        if is_eligible:
            discount_amount, _ = calculate_discount(coupon_code, float(total_amount))
            discount_amount = float(discount_amount)
            final_total = total_amount + shipping_charges - discount_amount
            
            return JsonResponse({
                'success': True,
                'message': f"Coupon '{coupon_code}' applied successfully! You saved ₹{discount_amount:.2f}",
                'discount_amount': discount_amount,
                'final_total': final_total,
                'applied_coupon': coupon_code
            })
        else:
            return JsonResponse({
                'success': False,
                'message': eligibility_message,
                'discount_amount': 0,
                'final_total': total_amount + shipping_charges,
                'applied_coupon': None
            })
    
    # For GET requests, redirect to checkout
    return redirect('checkout')


# ✅ 1. DOWNLOAD INVOICE (PDF)
@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, customer=request.user)

    try:
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        return HttpResponse("PDF generation is not available. Please contact support.", status=503)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.order_id}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph("<b>INVOICE</b>", styles['Title']))
    elements.append(Spacer(1, 20))

    # Order Details
    elements.append(Paragraph(f"<b>Order ID:</b> {order.order_id}", styles['Normal']))
    elements.append(Paragraph(f"<b>Date:</b> {order.created_at.strftime('%d %B %Y')}", styles['Normal']))
    elements.append(Paragraph(f"<b>Status:</b> {order.status}", styles['Normal']))
    elements.append(Spacer(1, 15))

    # Customer Details
    elements.append(Paragraph("<b>Customer Details</b>", styles['Heading3']))
    elements.append(Paragraph(f"{order.name}", styles['Normal']))
    elements.append(Paragraph(f"{request.user.email}", styles['Normal']))
    elements.append(Paragraph(f"{order.address}, {order.city}, {order.state}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Product Table
    data = [["Product", "Price"]]

    for product in order.products.all():
        data.append([product.name, f"₹{product.price}"])

    # Total row
    data.append(["Total", f"₹{order.total_amount}"])

    table = Table(data, colWidths=[300, 100])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.pink),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ]))

    elements.append(table)

    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Thank you for shopping with us ❤️", styles['Normal']))

    doc.build(elements)

    return response


# ✅ 2. CANCEL ORDER
@login_required
def cancel_order(request, order_id):
    """Cancel an order if status is pending or processing"""
    if request.method != "POST":
        return JsonResponse({
            "success": False, 
            "message": "Only POST requests are allowed"
        })
    
    try:
        order = get_object_or_404(Order, order_id=order_id, customer=request.user)
        print(f"🔄 Processing cancel request for order {order.order_id}")
        
        if order.status in ["pending", "processing"]:
            # Update status to cancelled using update_fields as specified
            order.status = "cancelled"
            order.save(update_fields=['status'])
            print(f"✅ Order {order.order_id} status updated to cancelled")
            
            return JsonResponse({
                "success": True, 
                "message": "Order cancelled successfully"
            })
        else:
            return JsonResponse({
                "success": False, 
                "message": "Cannot cancel this order"
            })
            
    except Order.DoesNotExist:
        print(f"❌ Order not found: {order_id}")
        return JsonResponse({
            "success": False, 
            "message": "Order not found"
        })
    except Exception as e:
        print(f"❌ Error in cancel_order: {str(e)}")
        return JsonResponse({
            "success": False, 
            "message": "An error occurred while processing your cancel request. Please try again."
        })


# 3. RETURN ORDER
@login_required
def return_order(request, order_id):
    """Handle return order request with comprehensive Decimal handling"""
    from datetime import datetime, timedelta
    from decimal import Decimal, InvalidOperation
    
    if request.method != 'POST':
        return JsonResponse({
            "success": False, 
            "message": "Only POST requests are allowed"
        })
    
    try:
        order = get_object_or_404(Order, order_id=order_id, customer=request.user)
        print(f"🔄 Processing return request for order {order.order_id}")
        
        if order.status == "delivered":
            # Use delivered_date if available, otherwise use created_at + estimated delivery time
            delivery_date = order.delivered_date or (order.created_at + timedelta(days=3))
            
            # Calculate return window (30 days from delivery)
            return_window = delivery_date + timedelta(days=30)
            
            if datetime.now().date() <= return_window.date():
                # Only update status field to avoid total_amount validation issues
                order.status = "return_requested"
                order.save(update_fields=['status'])
                print(f"✅ Order {order.order_id} status updated to return_requested")
                
                return JsonResponse({
                    "success": True, 
                    "message": "Return request submitted successfully"
                })
            else:
                return JsonResponse({
                    "success": False, 
                    "message": "Return window has expired (30 days from delivery)"
                })
        else:
            return JsonResponse({
                "success": False, 
                "message": "Only delivered orders can be returned"
            })
            
    except Order.DoesNotExist:
        print(f"❌ Order not found: {order_id}")
        return JsonResponse({
            "success": False, 
            "message": "Order not found"
        })
    except Exception as e:
        print(f"❌ Error in return_order: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        return JsonResponse({
            "success": False, 
            "message": "An error occurred while processing your return request. Please try again."
        })


# 4. MARK ORDER AS SHIPPED
@login_required
def mark_order_shipped(request, order_id):
    """Mark an order as shipped (for admin use)"""
    from django.utils import timezone
    
    try:
        order = get_object_or_404(Order, order_id=order_id)
        
        # Debug: Print order details
        print(f"🔍 Debug: Order {order.order_id}, customer: {order.customer}, current user: {request.user}")
        
        # Check if current user is the order customer or is staff
        if order.customer == request.user or request.user.is_staff:
            if order.status == "processing":
                order.status = "shipped"
                order.shipped_date = timezone.now()
                order.save()
                return JsonResponse({
                    "success": True, 
                    "message": f"Order {order.order_id} marked as shipped"
                })
            elif order.status == "shipped":
                return JsonResponse({
                    "success": False, 
                    "message": "Order is already shipped"
                })
            else:
                return JsonResponse({
                    "success": False, 
                    "message": f"Cannot mark order with status '{order.status}' as shipped"
                })
        else:
            return JsonResponse({
                "success": False, 
                "message": "You can only mark your own orders as shipped"
            })
            
    except Exception as e:
        print(f"❌ Error in mark_order_shipped: {e}")
        return JsonResponse({
            "success": False, 
            "message": f"Error: {str(e)}"
        })