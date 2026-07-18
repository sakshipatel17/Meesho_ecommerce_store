from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

class EmailAuthBackend(BaseBackend):
    """
    Custom authentication backend that allows users to login with their email address.
    Works with custom User model that has email as USERNAME_FIELD.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user using email as username.
        """
        User = get_user_model()
        
        try:
            # Get user by email (since USERNAME_FIELD is 'email')
            user = User.objects.get(email=username)
            
            # Check password
            if user.check_password(password):
                return user
                
        except User.DoesNotExist:
            return None
            
        return None
    
    def get_user(self, user_id):
        """
        Retrieve user by ID.
        """
        User = get_user_model()
        
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
