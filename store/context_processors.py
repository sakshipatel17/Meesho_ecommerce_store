from .models import Category, Product
from datetime import datetime


def categories_processor(request):
    """Provide top-level categories, their subcategories, and a few featured products.

    We attach a `featured_products` attribute to each top-level category so the
    template can show small product thumbnails in the megamenu.
    """
    try:
        categories = list(Category.objects.filter(parent__isnull=True).prefetch_related('subcategories'))
        # Attach featured products for each category (top 3 newest products within category + subcategories)
        for cat in categories:
            try:
                sub_ids = [s.id for s in cat.subcategories.all()]
                ids = [cat.id] + sub_ids
                # Djongo may not support ORDER BY in all contexts; fetch candidates and sort in Python
                candidates = list(Product.objects.filter(category__id__in=ids))
                featured = sorted(
                    candidates,
                    key=lambda p: p.created_at if getattr(p, 'created_at', None) is not None else datetime.min,
                    reverse=True
                )[:4]
            except Exception:
                featured = []
            # attach attribute for template access
            cat.featured_products = featured
        # Move 'Women Clothing' (or any category containing 'women') to the front so it appears first
        try:
            idx = next(i for i, c in enumerate(categories) if 'women' in (c.name or '').lower())
            if idx != 0:
                women_cat = categories.pop(idx)
                categories.insert(0, women_cat)
        except StopIteration:
            pass
    except Exception:
        categories = []
    return {
        'nav_categories': categories
    }


def cart_count(request):
    """
    Context processor to provide cart item count for both authenticated and guest users
    """
    if request.user.is_authenticated:
        try:
            from .models import CartItem
            count = CartItem.objects.filter(cart__user=request.user).count()
        except:
            count = 0
    else:
        # For guest users, count items in session cart
        cart = request.session.get('cart', [])
        count = len(cart) if isinstance(cart, list) else 0
    
    return {'cart_count': count}
