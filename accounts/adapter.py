from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from .models import User

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form):
        # Override to use your custom User model
        return super().save_user(request, user, form)

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        This is called when a user successfully authenticates via a social provider.
        """
        # If the user already exists, just return
        if sociallogin.is_existing:
            return
        
        # Get the email from the social account
        email = sociallogin.account.extra_data.get('email')
        if not email:
            return
        
        # Check if user with this email already exists
        try:
            user = User.objects.get(email=email)
            # Link the social account to the existing user
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            # User doesn't exist, will be created automatically
            pass

    def save_user(self, request, sociallogin, form=None):
        """
        This is called when a new user is created via social login.
        """
        user = super().save_user(request, sociallogin, form)
        
        # Set additional fields if needed
        if sociallogin.account.provider == 'google':
            # Get user data from Google
            extra_data = sociallogin.account.extra_data
            user.name = extra_data.get('name', '')
            user.is_verified = True  # Google users are considered verified
            user.save()
        
        return user
