from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import (
    Product, UserBehavior, AIRecommendation, WishlistItem, 
    SmartOffer, SellerTrustScore, Review, Order
)
import random
import math

class AIRecommendationEngine:
    """AI-powered recommendation engine"""
    
    @staticmethod
    def track_user_behavior(user, product, action_type, session_id=None):
        """Track user behavior for AI learning"""
        if user.is_authenticated:
            try:
                behavior = UserBehavior.objects.get(
                    user=user,
                    product=product,
                    action_type=action_type,
                    session_id=session_id
                )
            except UserBehavior.DoesNotExist:
                UserBehavior.objects.create(
                    user=user,
                    product=product,
                    action_type=action_type,
                    session_id=session_id,
                    timestamp=timezone.now()
                )
            except Exception as e:
                print(f"Error tracking user behavior: {e}")
    
    @staticmethod
    def get_personalized_recommendations(user, limit=10):
        """Get personalized product recommendations for user"""
        if not user.is_authenticated:
            return AIRecommendationEngine.get_trending_products(limit)
        
        # Get user's behavior history
        user_behaviors = UserBehavior.objects.filter(user=user)
        
        # Get frequently viewed categories
        viewed_products = Product.objects.filter(
            userbehavior__user=user,
            userbehavior__action_type='view'
        ).distinct()
        
        # Get wishlist items
        wishlist_products = Product.objects.filter(
            wishlistitem__user=user,
            wishlistitem__is_active=True
        )
        
        # Get purchased items
        purchased_products = Product.objects.filter(
            order_products__customer=user
        ).distinct()
        
        recommendations = []
        
        # 1. Similar to wishlist items
        for product in wishlist_products:
            similar = AIRecommendationEngine.get_similar_products(product, exclude_user=user)
            recommendations.extend(similar[:2])
        
        # 2. Similar to purchased items
        for product in purchased_products:
            similar = AIRecommendationEngine.get_similar_products(product, exclude_user=user)
            recommendations.extend(similar[:1])
        
        # 3. Trending in viewed categories
        if viewed_products:
            categories = viewed_products.values_list('category', flat=True).distinct()
            trending = Product.objects.filter(
                category__in=categories
            ).exclude(
                Q(order_products__customer=user) |
                Q(wishlistitem__user=user)
            ).annotate(
                view_count=Count('userbehavior', filter=Q(userbehavior__action_type='view'))
            ).order_by('-view_count')[:5]
            
            recommendations.extend(trending)
        
        # Remove duplicates and limit
        unique_recommendations = list(dict.fromkeys(recommendations))[:limit]
        
        # Save recommendations to database
        for product in unique_recommendations:
            try:
                AIRecommendation.objects.get(
                    user=user,
                    product=product,
                    recommendation_type='personalized'
                )
            except AIRecommendation.DoesNotExist:
                AIRecommendation.objects.create(
                    user=user,
                    product=product,
                    recommendation_type='personalized',
                    score=random.uniform(0.7, 0.95)
                )
            except Exception as e:
                print(f"Error saving recommendation: {e}")
        
        return unique_recommendations
    
    @staticmethod
    def get_similar_products(product, limit=5, exclude_user=None):
        """Get similar products based on category and attributes"""
        similar = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)
        
        if exclude_user:
            similar = similar.exclude(
                Q(order_products__customer=exclude_user) |
                Q(wishlistitem__user=exclude_user)
            )
        
        return similar[:limit]
    
    @staticmethod
    def get_trending_products(limit=10):
        """Get trending products based on recent activity"""
        recent_date = timezone.now() - timedelta(days=7)
        
        trending = Product.objects.filter(
            userbehavior__timestamp__gte=recent_date
        ).annotate(
            view_count=Count('userbehavior', filter=Q(userbehavior__action_type='view')),
            wishlist_count=Count('userbehavior', filter=Q(userbehavior__action_type='wishlist'))
        ).annotate(
            trending_score=Count('userbehavior')
        ).order_by('-trending_score')[:limit]
        
        return trending

class SmartWishlistManager:
    """Smart wishlist with AI-powered notifications"""
    
    @staticmethod
    def add_to_wishlist(user, product):
        """Add product to wishlist with tracking"""
        try:
            wishlist_item = WishlistItem.objects.get(
                user=user,
                product=product
            )
            wishlist_item.is_active = True
            wishlist_item.save()
            created = False
        except WishlistItem.DoesNotExist:
            wishlist_item = WishlistItem.objects.create(
                user=user,
                product=product,
                is_active=True
            )
            created = True
        except Exception as e:
            print(f"Error managing wishlist: {e}")
            return
        
        if created:
            # Track behavior
            AIRecommendationEngine.track_user_behavior(user, product, 'wishlist')
            
            # Check for smart offer trigger
            SmartOfferEngine.check_and_create_offer(user, product, 'wishlist_add')
        
        return wishlist_item
    
    @staticmethod
    def remove_from_wishlist(user, product):
        """Remove from wishlist and track feedback"""
        try:
            wishlist_item = WishlistItem.objects.get(user=user, product=product)
            wishlist_item.is_active = False
            wishlist_item.save()
            
            # Track behavior
            AIRecommendationEngine.track_user_behavior(user, product, 'wishlist_remove')
            
            # Get similar products as suggestions
            similar_products = AIRecommendationEngine.get_similar_products(product, limit=3)
            
            return {
                'removed': True,
                'suggestions': similar_products,
                'feedback_request': True
            }
        except WishlistItem.DoesNotExist:
            return {'removed': False}
    
    @staticmethod
    def check_wishlist_reminders():
        """Check for wishlist items that need reminders"""
        reminder_date = timezone.now() - timedelta(days=3)
        
        items_to_remind = WishlistItem.objects.filter(
            is_active=True,
            added_at__lte=reminder_date
        ).filter(
            Q(last_notified__isnull=True) | 
            Q(last_notified__lte=timezone.now() - timedelta(days=2))
        )
        
        reminders = []
        for item in items_to_remind:
            if item.notification_count < 2:  # Max 2 reminders
                reminders.append({
                    'user': item.user,
                    'product': item.product,
                    'days_in_wishlist': (timezone.now() - item.added_at).days
                })
                
                # Update notification tracking
                item.last_notified = timezone.now()
                item.notification_count += 1
                item.save()
        
        return reminders

class SmartOfferEngine:
    """AI-powered smart offers and discounts"""
    
    @staticmethod
    def check_and_create_offer(user, product=None, trigger_reason='general'):
        """Check if user qualifies for smart offer"""
        # Check user's viewing frequency
        view_count = UserBehavior.objects.filter(
            user=user,
            product=product,
            action_type='view'
        ).count() if product else 0
        
        # Check wishlist duration
        if product:
            try:
                wishlist_item = WishlistItem.objects.get(user=user, product=product, is_active=True)
                days_in_wishlist = (timezone.now() - wishlist_item.added_at).days
                
                # Create offer if viewed 3+ times or in wishlist for 5+ days
                if view_count >= 3 or days_in_wishlist >= 5:
                    return SmartOfferEngine.create_personalized_offer(
                        user, product, trigger_reason
                    )
            except WishlistItem.DoesNotExist:
                pass
        
        return None
    
    @staticmethod
    def create_personalized_offer(user, product, trigger_reason):
        """Create personalized offer"""
        discount_percentage = random.uniform(10, 25)  # 10-25% discount
        expires_at = timezone.now() + timedelta(days=3)  # 3-day expiry
        
        offer = SmartOffer.objects.create(
            user=user,
            product=product,
            offer_type='discount',
            discount_percentage=discount_percentage,
            expires_at=expires_at,
            trigger_reason=trigger_reason
        )
        
        return offer
    
    @staticmethod
    def get_user_offers(user):
        """Get active offers for user"""
        return SmartOffer.objects.filter(
            user=user,
            is_used=False,
            expires_at__gt=timezone.now()
        ).order_by('created_at')

class SellerTrustEngine:
    """AI-powered seller trust and fake detection system"""
    
    @staticmethod
    def calculate_trust_score(user):
        """Calculate trust score for seller/user"""
        # Get user's products
        products = Product.objects.filter(order_products__customer=user).distinct()
        
        if not products:
            return SellerTrustScore.objects.create(
                user=user,
                trust_score=50.0,  # Default score
                total_ratings=0,
                average_rating=0.0
            )
        
        # Calculate metrics
        total_ratings = Review.objects.filter(product__in=products).count()
        avg_rating = Review.objects.filter(product__in=products).aggregate(
            avg=Avg('rating')
        )['avg'] or 0
        
        # Calculate return rate (mock data - in real app, track returns)
        return_rate = random.uniform(0, 10)  # 0-10% return rate
        
        # Fake review detection (simplified)
        fake_review_prob = SellerTrustEngine.detect_fake_reviews(products)
        
        # Calculate trust score (0-100)
        trust_score = min(100, max(0, (
            (avg_rating / 5) * 40 +  # Rating weight: 40%
            (100 - return_rate) * 0.3 +  # Return rate weight: 30%
            (100 - fake_review_prob) * 0.3  # Review authenticity: 30%
        )))
        
        # Update or create trust score
        trust_score_obj, created = SellerTrustScore.objects.update_or_create(
            user=user,
            defaults={
                'trust_score': trust_score,
                'total_ratings': total_ratings,
                'average_rating': avg_rating or 0,
                'return_rate': return_rate,
                'fake_review_probability': fake_review_prob,
                'is_verified': trust_score >= 70
            }
        )
        
        return trust_score_obj
    
    @staticmethod
    def detect_fake_reviews(products):
        """Detect potentially fake reviews (simplified AI)"""
        fake_indicators = 0
        total_reviews = 0
        
        for product in products:
            reviews = Review.objects.filter(product=product)
            total_reviews += reviews.count()
            
            for review in reviews:
                # Check for fake review indicators
                if len(review.comment) < 10:  # Very short reviews
                    fake_indicators += 1
                elif review.rating == 5 and not review.comment:  # 5-star with no comment
                    fake_indicators += 0.5
                elif 'excellent' in review.comment.lower() and 'perfect' in review.comment.lower():
                    fake_indicators += 0.3
        
        if total_reviews == 0:
            return 0
        
        return min(100, (fake_indicators / total_reviews) * 100)

class VoiceSearchEngine:
    """Voice search processing"""
    
    @staticmethod
    def process_voice_search(user, query_text, session_id=None):
        """Process voice search query"""
        # Extract keywords and intent
        keywords = VoiceSearchEngine.extract_keywords(query_text)
        
        # Search products
        products = Product.objects.filter(
            Q(name__icontains=keywords) |
            Q(description__icontains=keywords) |
            Q(category__name__icontains=keywords)
        )
        
        # Track voice search
        VoiceSearch.objects.create(
            user=user if user.is_authenticated else None,
            query_text=query_text,
            search_results_count=products.count(),
            session_id=session_id
        )
        
        return products
    
    @staticmethod
    def extract_keywords(query_text):
        """Extract keywords from voice query"""
        # Simple keyword extraction (can be enhanced with NLP)
        stop_words = ['show', 'me', 'find', 'i', 'want', 'to', 'under', 'for', 'the', 'a', 'an']
        words = query_text.lower().split()
        keywords = [word for word in words if word not in stop_words]
        return ' '.join(keywords)

class VirtualTryOnEngine:
    """Virtual try-on processing"""
    
    @staticmethod
    def create_try_on_session(user, product, user_image, try_on_type):
        """Create virtual try-on session"""
        session = VirtualTryOn.objects.create(
            user=user,
            product=product,
            user_image=user_image,
            try_on_type=try_on_type
        )
        
        # In a real implementation, this would process the image with AI
        # For now, we'll mark it as processed after a delay
        session.is_processed = True
        session.save()
        
        return session
