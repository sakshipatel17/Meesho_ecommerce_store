from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from .models import Product, WishlistItem, SmartOffer, AIRecommendation, VirtualTryOn, VoiceSearch
from .ai_helper import (
    AIRecommendationEngine, SmartWishlistManager, SmartOfferEngine,
    SellerTrustEngine, VoiceSearchEngine, VirtualTryOnEngine
)
import json

@login_required
def ai_recommendations(request):
    """Get AI-powered product recommendations"""
    recommendations = AIRecommendationEngine.get_personalized_recommendations(request.user, limit=8)
    
    return JsonResponse({
        'success': True,
        'recommendations': [
            {
                'id': str(product.id),
                'name': product.name,
                'price': float(product.price),
                'image': product.image.url if product.image else None,
                'slug': product.slug,
                'category': product.category.name
            }
            for product in recommendations
        ]
    })

@login_required
def smart_wishlist_add(request, product_id):
    """Add product to smart wishlist"""
    product = get_object_or_404(Product, id=product_id)
    wishlist_item = SmartWishlistManager.add_to_wishlist(request.user, product)
    
    return JsonResponse({
        'success': True,
        'message': 'Added to wishlist!',
        'in_wishlist': True
    })

@login_required
def smart_wishlist_remove(request, product_id):
    """Remove product from smart wishlist with suggestions"""
    product = get_object_or_404(Product, id=product_id)
    result = SmartWishlistManager.remove_from_wishlist(request.user, product)
    
    response_data = {
        'success': result.get('removed', False),
        'message': 'Removed from wishlist',
        'feedback_request': result.get('feedback_request', False)
    }
    
    if result.get('suggestions'):
        response_data['suggestions'] = [
            {
                'id': str(p.id),
                'name': p.name,
                'price': float(p.price),
                'image': p.image.url if p.image else None,
                'slug': p.slug
            }
            for p in result['suggestions']
        ]
    
    return JsonResponse(response_data)

@login_required
def smart_offers(request):
    """Get user's smart offers"""
    offers = SmartOfferEngine.get_user_offers(request.user)
    
    return JsonResponse({
        'success': True,
        'offers': [
            {
                'id': offer.id,
                'type': offer.offer_type,
                'discount': offer.discount_percentage,
                'product': {
                    'id': str(offer.product.id),
                    'name': offer.product.name,
                    'price': float(offer.product.price),
                    'image': offer.product.image.url if offer.product.image else None
                } if offer.product else None,
                'expires_at': offer.expires_at.isoformat(),
                'trigger_reason': offer.trigger_reason
            }
            for offer in offers
        ]
    })

@login_required
def wishlist_reminders(request):
    """Check and return wishlist reminders"""
    reminders = SmartWishlistManager.check_wishlist_reminders()
    user_reminders = [r for r in reminders if r['user'] == request.user]
    
    return JsonResponse({
        'success': True,
        'reminders': [
            {
                'product_id': str(r['product'].id),
                'product_name': r['product'].name,
                'days_in_wishlist': r['days_in_wishlist'],
                'message': f"Still interested in {r['product'].name}? You added it {r['days_in_wishlist']} days ago!"
            }
            for r in user_reminders
        ]
    })

def seller_trust_score(request, user_id):
    """Get seller trust score"""
    from accounts.models import User
    seller = get_object_or_404(User, id=user_id)
    trust_score = SellerTrustEngine.calculate_trust_score(seller)
    
    return JsonResponse({
        'success': True,
        'trust_score': trust_score.trust_score,
        'is_verified': trust_score.is_verified,
        'total_ratings': trust_score.total_ratings,
        'average_rating': trust_score.average_rating,
        'return_rate': trust_score.return_rate,
        'fake_review_probability': trust_score.fake_review_probability
    })

@csrf_exempt
def voice_search(request):
    """Handle voice search requests"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query_text = data.get('query', '')
            session_id = request.session.session_key
            
            products = VoiceSearchEngine.process_voice_search(
                request.user, query_text, session_id
            )
            
            return JsonResponse({
                'success': True,
                'query': query_text,
                'results_count': products.count(),
                'products': [
                    {
                        'id': str(product.id),
                        'name': product.name,
                        'price': float(product.price),
                        'image': product.image.url if product.image else None,
                        'slug': product.slug,
                        'category': product.category.name
                    }
                    for product in products
                ]
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def virtual_try_on(request, product_id):
    """Handle virtual try-on requests"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        
        # Handle uploaded image
        if 'user_image' in request.FILES:
            user_image = request.FILES['user_image']
            try_on_type = request.POST.get('try_on_type', 'clothing')
            
            session = VirtualTryOnEngine.create_try_on_session(
                request.user, product, user_image, try_on_type
            )
            
            return JsonResponse({
                'success': True,
                'session_id': session.id,
                'message': 'Virtual try-on created successfully!',
                'result_image': session.result_image.url if session.result_image else None
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No image provided'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def trending_products(request):
    """Get trending products"""
    products = AIRecommendationEngine.get_trending_products(limit=12)
    
    return JsonResponse({
        'success': True,
        'products': [
            {
                'id': str(product.id),
                'name': product.name,
                'price': float(product.price),
                'image': product.image.url if product.image else None,
                'slug': product.slug,
                'category': product.category.name,
                'view_count': getattr(product, 'view_count', 0),
                'wishlist_count': getattr(product, 'wishlist_count', 0)
            }
            for product in products
        ]
    })

@login_required
def track_user_behavior(request):
    """Track user behavior for AI learning"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            action_type = data.get('action_type')
            
            product = get_object_or_404(Product, id=product_id)
            session_id = request.session.session_key
            
            AIRecommendationEngine.track_user_behavior(
                request.user, product, action_type, session_id
            )
            
            # Check for smart offers
            offers = []
            if action_type in ['view', 'wishlist']:
                offer = SmartOfferEngine.check_and_create_offer(
                    request.user, product, f'{action_type}_trigger'
                )
                if offer:
                    offers.append({
                        'id': offer.id,
                        'type': offer.offer_type,
                        'discount': offer.discount_percentage,
                        'message': f"Special offer just for you! {offer.discount_percentage}% off!"
                    })
            
            return JsonResponse({
                'success': True,
                'offers': offers
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def similar_products(request, product_id):
    """Get similar products for a given product"""
    product = get_object_or_404(Product, id=product_id)
    similar = AIRecommendationEngine.get_similar_products(product, limit=6)
    
    return JsonResponse({
        'success': True,
        'similar_products': [
            {
                'id': str(p.id),
                'name': p.name,
                'price': float(p.price),
                'image': p.image.url if p.image else None,
                'slug': p.slug,
                'category': p.category.name
            }
            for p in similar
        ]
    })

@login_required
def recommendation_feedback(request):
    """Handle feedback on AI recommendations"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            recommendation_id = data.get('recommendation_id')
            feedback_type = data.get('feedback_type')  # 'click', 'not_interested'
            
            recommendation = get_object_or_404(AIRecommendation, id=recommendation_id)
            
            if feedback_type == 'click':
                recommendation.is_clicked = True
                recommendation.clicked_at = timezone.now()
                recommendation.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
