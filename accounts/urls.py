from django.urls import path
from django.shortcuts import render
from . import views

urlpatterns = [
    path("register/",views.register,name="register"),
    path("login/",views.login_view,name="login"),
    path("logout/",views.logout_view,name="logout"),
    path("forgot-password/",views.forgot_password,name="forgot_password"),
    path("reset-password/<token>/",views.reset_password,name="reset_password"),
    path("debug/", lambda request: render(request, 'debug_oauth.html'), name="oauth_debug"),
]
