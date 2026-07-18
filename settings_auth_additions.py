# Add this to your settings.py AUTHENTICATION_BACKENDS

AUTHENTICATION_BACKENDS = [
    'accounts.auth_backends.EmailAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Also add these if not already present
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Email settings (for password reset)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'

# For development, you can use console backend
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
