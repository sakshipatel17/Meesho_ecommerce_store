from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model

@login_required
def debug_social_auth(request):
    """Debug view to check social authentication status"""
    user = request.user
    social_accounts = SocialAccount.objects.filter(user=user)
    
    context = {
        'user': user,
        'social_accounts': social_accounts,
        'is_authenticated': user.is_authenticated,
    }
    
    return render(request, 'debug_social.html', context)
