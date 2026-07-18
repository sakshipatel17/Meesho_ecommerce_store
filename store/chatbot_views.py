from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json


@csrf_exempt
@require_http_methods(["POST"])
def chatbot_response(request):
    """
    Simple chatbot with predefined responses - NO AI, NO DATABASE CALLS
    Only basic keyword matching and static responses
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip().lower()
        
        # Empty message check
        if not user_message:
            return JsonResponse({
                'success': True,
                'response': 'Please type a message to continue.',
                'quick_replies': ['Hi', 'Orders', 'Payment', 'Offers']
            })
        
        # Get response based on keywords
        response = get_predefined_response(user_message, request.user)
        
        return JsonResponse({
            'success': True,
            'response': response['message'],
            'quick_replies': response.get('quick_replies', ['Help', 'Hi', 'Back'])
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': True,
            'response': "Sorry, something went wrong. Please try again.",
            'quick_replies': ['Hi', 'Help']
        })


def get_predefined_response(message, user):
    """
    AI-like smart chatbot (NO REAL AI, NO EXTERNAL APIS)
    Rich interactions with mood detection, time awareness, and personalization
    """

    message = message.lower().strip()
    
    # Simple variation counter using message hash to avoid repetition
    import hashlib
    msg_hash = int(hashlib.md5((message + str(user.id if user.is_authenticated else 'anon')).encode()).hexdigest()[:8], 16)
    variation = msg_hash % 2  # 0 or 1 for alternating responses
    
    # Time-based greeting
    from datetime import datetime
    current_hour = datetime.now().hour
    time_greeting = "Good morning" if 5 <= current_hour < 12 else "Good evening" if 17 <= current_hour <= 23 else "Good afternoon"
    
    # Personalization
    username = user.username.split('@')[0] if user and user.is_authenticated else "there"
    
    # Mood detection - apology tone for frustrated users
    frustrated_words = ['late', 'delay', 'angry', 'not received', 'delayed', 'slow', 'frustrated', 'annoyed', 'worried']
    is_frustrated = any(word in message for word in frustrated_words)
    
    # Bored detection
    is_bored = any(word in message for word in ['bored', 'boring', 'nothing to do', 'free time'])

    # Handle "enter order id" specifically
    if 'enter order id' in message:
        return {
            'message': f'📦 Please type your Order ID (for example: #123456) so I can track it for you, {username}.',
            'quick_replies': ['Payment Help', 'Offers', 'Back']
        }

    # Order ID detection with progress
    if message.startswith('#') or (message.isdigit() and len(message) >= 5):
        try:
            order_id = message.lstrip('#')
            order_id = int(order_id)

            from store.models import Order
            order = Order.objects.filter(order_id=str(order_id)).first()

            if not order:
                order = Order.objects.filter(tracking_id=str(order_id)).first()

            if order:
                # Mood-aware response
                if is_frustrated:
                    apology = "I sincerely apologize for the delay. "
                else:
                    apology = ""

                # Progress display based on status
                if order.status == "return_requested":
                    progress = "✔ Order Placed\n✔ Processing\n✔ Return Requested\n⏳ Processing Return"
                    return {
                        'message': f'{apology}🔁 Your return request for order #{order_id} is submitted.\n\n{progress}\n\n💡 Need anything else, {username}?',
                        'quick_replies': ['Track Another', 'Help', 'Offers']
                    }

                elif order.status == "delivered":
                    progress = "✔ Order Placed\n✔ Processing\n🚚 Out for Delivery\n✔ Delivered"
                    return {
                        'message': f'{apology}✅ Your order #{order_id} has been delivered successfully!\n\n{progress}\n\n🎉 Enjoy your purchase, {username}! Need more items?',
                        'quick_replies': ['Shop Again', 'Help', 'Offers']
                    }

                elif order.status == "pending":
                    progress = "✔ Order Placed\n⏳ Pending Confirmation\n📦 Awaiting Processing"
                    return {
                        'message': f'{apology}⏳ Your order #{order_id} is still pending.\n\n{progress}\n\n💡 While waiting, check out today\'s deals!',
                        'quick_replies': ['View Offers', 'Track Another', 'Help']
                    }

                else:  # processing
                    progress = "✔ Order Placed\n🔄 Processing\n📦 Getting Ready"
                    return {
                        'message': f'{apology}📦 Your order #{order_id} is being processed.\n\n{progress}\n\n🚀 Expected delivery: 3-5 days',
                        'quick_replies': ['Track Another', 'View Offers', 'Help']
                    }
            else:
                return {
                    'message': f'❌ Order #{order_id} not found. Let me help you find it, {username}! Check your email for the correct ID.',
                    'quick_replies': ['Orders', 'Help']
                }

        except:
            return {
                'message': f'⚠️ Unable to fetch order right now, {username}. Please try again in a moment.',
                'quick_replies': ['Orders', 'Help']
            }

    # Bored response - suggest shopping
    if is_bored:
        if variation == 0:
            return {
                'message': f'🎯 Feeling bored, {username}? Let\'s make it exciting! How about:\n\n🛍️ Explore new arrivals\n🎁 Check today\'s offers\n📱 Play with our product finder\n\nWhat sounds fun?',
                'quick_replies': ['Shop Now', 'Today\'s Deals', 'Product Finder']
            }
        else:
            return {
                'message': f'🌟 Boredom alert! Perfect time for shopping, {username}! \n\n💎 Discover trending items\n🏆 Win amazing deals\n🎯 Find your perfect match\n\nReady to explore?',
                'quick_replies': ['Trending Now', 'Hot Deals', 'Help Me Choose']
            }

    # Enhanced greeting with time and personalization
    if any(word in message for word in ['hi', 'hello', 'hey', 'hii', 'hiii']):
        if is_frustrated:
            return {
                'message': f'🙏 {time_greeting}, {username}! I sense you might be frustrated. I\'m here to help resolve any issues. What\'s concerning you?',
                'quick_replies': ['Track Order', 'Payment Issue', 'Talk to Support']
            }
        else:
            if variation == 0:
                return {
                    'message': f'🌅 {time_greeting}, {username}! Great to connect! How can I make your day amazing today? 😊',
                    'quick_replies': ['Orders', 'Payment', 'Offers', 'Products']
                }
            else:
                return {
                    'message': f'✨ {time_greeting}, {username}! Welcome back! What adventure shall we embark on today? 🎯',
                    'quick_replies': ['Quick Shopping', 'Order Status', 'Today\'s Deals', 'Help']
                }

    # Order related with mood awareness
    if any(word in message for word in ['order', 'track', 'delivery', 'status']) and 'enter order id' not in message:
        if is_frustrated:
            return {
                'message': f'🙏 I understand your concern, {username}. Let me help track your order immediately. Please share your Order ID and I\'ll check the status for you.',
                'quick_replies': ['Enter Order ID', 'Urgent Help', 'Back']
            }
        else:
            if variation == 0:
                return {
                    'message': f'📦 Happy to help track your order, {username}! Just type your Order ID (like #123456) and I\'ll find it instantly. 🔍',
                    'quick_replies': ['Enter Order ID', 'Payment Help', 'Back']
                }
            else:
                return {
                    'message': f'🎯 Let\'s track your order, {username}! Share the Order ID and I\'ll get you the latest status right away. 📋',
                    'quick_replies': ['Enter Order ID', 'View Orders', 'Back']
                }

    # Enhanced payment system
    if any(word in message for word in ['payment', 'pay', 'upi', 'cash', 'cod', 'card', 'credit card', 'debit card', 'online payment', 'transaction']):
        # UPI specific
        if 'upi' in message:
            return {
                'message': f'📱 Perfect choice, {username}! UPI is super fast - payment completes in seconds with PhonePe, GPay, or PayTM. ⚡\n\n🚀 90% users prefer UPI for instant checkout!',
                'quick_replies': ['Complete Payment', 'Other Options', 'Help']
            }
        
        # Card specific
        elif 'card' in message or 'cards' in message:
            return {
                'message': f'💳 Great option, {username}! We accept all major debit and credit cards with 100% secure checkout. Your data is safe with us! 🔒',
                'quick_replies': ['Pay with Card', 'Other Options', 'Security Info']
            }
        
        # Cash/COD specific
        elif 'cash' in message or 'cod' in message:
            return {
                'message': f'💵 Smart choice, {username}! Pay only when you receive. Cash on Delivery available nationwide - no upfront payment needed! 🏠',
                'quick_replies': ['Choose COD', 'Other Options', 'Delivery Info']
            }
        
        # Interactive payment choice
        else:
            if variation == 0:
                return {
                    'message': f'💳 Choose your perfect payment method, {username}:\n\n📱 **UPI** - Instant & Secure\n💳 **Card** - All Types Accepted\n💵 **COD** - Pay on Delivery\n\n🚀 90% users prefer UPI for faster checkout!\n\nWhich one do you prefer?',
                    'quick_replies': ['UPI', 'Card', 'COD', 'Back']
                }
            else:
                return {
                    'message': f'💰 Select your payment option, {username}:\n\n📱 **UPI** - Fast & Easy (Recommended)\n💳 **Card** - Safe Checkout\n💵 **Cash on Delivery** - Pay When Arrives\n\n⭐ Pro tip: UPI completes in seconds!\n\nWhich one do you prefer?',
                    'quick_replies': ['UPI', 'Card', 'Cash on Delivery', 'Back']
                }

    # Enhanced offers with smart suggestions
    if any(word in message for word in ['offer', 'discount', 'deal', 'coupon']):
        if variation == 0:
            return {
                'message': f'🎁 Exciting offers for you, {username}!\n\n1. 🔥 50% OFF on Women Clothing\n2. 💸 Flat ₹100 OFF on orders above ₹999\n3. 🚚 Free Delivery on your first order\n\n💡 Based on your interests, you might also love our electronics collection!',
                'quick_replies': ['Shop Women', 'View Electronics', 'All Deals']
            }
        else:
            return {
                'message': f'🏆 Amazing deals waiting, {username}!\n\n1. 🎉 Buy 1 Get 1 on Accessories\n2. ⭐ 30% OFF on Electronics\n3. 🎁 Extra 10% OFF with code SAVE10\n\n🎯 Since you\'re looking for deals, check out our flash sales too!',
                'quick_replies': ['Flash Sales', 'Accessories', 'Help']
            }

    # Enhanced products with suggestions
    if any(word in message for word in ['product', 'shop', 'buy', 'search', 'browse']):
        if variation == 0:
            return {
                'message': f'🛍️ Let\'s find something amazing for you, {username}! We\'ve got:\n\n👗 Women\'s Fashion - Trendy & Affordable\n💎 Accessories - Complete Your Look\n🏠 Home & Kitchen - Make Life Better\n📱 Electronics - Latest Gadgets\n\n💡 Based on current trends, Women\'s Fashion is hot right now!',
                'quick_replies': ['Women Fashion', 'Trending Items', 'Help Me Choose']
            }
        else:
            return {
                'message': f'🎯 Perfect time to shop, {username}! Explore our collections:\n\n🌟 Premium Women\'s Wear\n⚡ Smart Electronics\n🏡 Home Essentials\n💍 Beautiful Accessories\n\n🚀 Pro tip: Check out today\'s combo deals for extra savings!',
                'quick_replies': ['Combo Deals', 'New Arrivals', 'Personalized Picks']
            }

    # Enhanced help with smart suggestions
    if any(word in message for word in ['help', 'support', 'assist']):
        if is_frustrated:
            return {
                'message': f'🙏 I\'m here to help you, {username}. I can see you might need urgent assistance. Let me resolve this:\n\n📦 Order Issues - Track & Resolve\n💳 Payment Problems - Quick Solutions\n🚚 Delivery Concerns - Real-time Updates\n🎁 Offer Questions - Best Deals\n\nWhat\'s your main concern?',
                'quick_replies': ['Urgent Order Help', 'Payment Issue', 'Talk to Human']
            }
        else:
            if variation == 0:
                return {
                    'message': f'🤝 I\'ve got your back, {username}! Here\'s how I can help:\n\n📦 Order Tracking & Status\n💳 Payment Methods & Issues\n🎁 Current Offers & Coupons\n🛍️ Product Recommendations\n🚚 Delivery Information\n\nWhat would you like to explore?',
                    'quick_replies': ['Track Order', 'Payment Help', 'Today\'s Deals', 'Product Finder']
                }
            else:
                return {
                    'message': f'💪 Absolutely here to help, {username}! Choose your need:\n\n🎯 Quick Order Status\n💡 Payment Guidance\n🏆 Best Offers Today\n🛍️ Shopping Assistant\n📞 Connect to Support\n\nHow can I assist you best?',
                    'quick_replies': ['Quick Help', 'Shopping Guide', 'Contact Support']
                }

    # Enhanced back with smart suggestions
    if any(word in message for word in ['back', 'menu', 'home']):
        if variation == 0:
            return {
                'message': f'🏠 Welcome back, {username}! Ready for your next adventure? I\'ve got some fresh recommendations for you!\n\n🔥 Trending: Women\'s Fashion Sale\n🚀 Hot Deal: Electronics Combo\n🎁 New Offer: Free Shipping Today',
                'quick_replies': ['Check Trending', 'View Hot Deals', 'Main Menu']
            }
        else:
            return {
                'message': f'🌟 Great to see you again, {username}! What can we explore together today?\n\n🎯 Quick Shop - Popular Items\n📋 Your Orders - Status Check\n🏆 Today\'s Best - Top Deals\n💬 Chat More - I\'m here!',
                'quick_replies': ['Quick Shop', 'Order Status', 'Today\'s Best']
            }

    # Enhanced fallback with smart suggestions
    if variation == 0:
        return {
            'message': f'🤔 Let me help you better, {username}! Try these popular options:\n\n📦 Track your order status\n💳 Explore payment methods\n🎁 Discover amazing offers\n🛍️ Find perfect products\n\nOr simply type "help" and I\'ll guide you! 😊',
            'quick_replies': ['Track Order', 'View Offers', 'Shop Now', 'Help']
        }
    else:
        return {
            'message': f'🎯 I\'m here to assist you, {username}! Here are some quick ways I can help:\n\n🚀 Quick Order Tracking\n💰 Payment Solutions\n🏆 Today\'s Top Deals\n🎯 Personalized Shopping\n\nWhat interests you most right now?',
            'quick_replies': ['Order Status', 'Payment Help', 'Hot Deals', 'Shopping']
        }

