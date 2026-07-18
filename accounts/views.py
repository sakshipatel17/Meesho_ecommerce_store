from django.shortcuts import render,redirect
from .models import User
from .helper import send_password_reset_email
import uuid
from django.urls import reverse
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import login, authenticate,logout
from django.contrib.auth.decorators import login_required

def register(request):
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        password2 = request.POST.get('confirm-password', '').strip()
        
        # Validation
        if not email or not password or not password2:
            messages.error(request, 'All fields are required')
            return render(request,'accounts/signup.html')
        
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return render(request,'accounts/signup.html')
        
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
            return render(request,'accounts/signup.html')
        
        # Check if user already exists
        try:
            User.objects.get(email=email)
            messages.error(request, 'User with this email already exists')
            return render(request,'accounts/signup.html')
        except User.DoesNotExist:
            pass  # User doesn't exist, which is good
        except Exception as e:
            messages.error(request, f'Error checking user: {str(e)}')
            return render(request,'accounts/signup.html')
        
        try:
            # Create user using the manager
            user = User.objects.create_user(
                email=email,
                password=password
            )
            
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request,'accounts/signup.html')
        
    return render(request,'accounts/signup.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == "POST":
        email = request.POST.get("username", '').strip()  # Form uses name="username"
        password = request.POST.get("password", '').strip()
        
        if not email or not password:
            messages.error(request, 'Email and password are required')
            return render(request, 'accounts/login.html')
        
        try:
            # Try to authenticate using Django's authenticate function
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, 'Login successful!')
                    
                    # Redirect to next page if available, otherwise home
                    next_url = request.GET.get('next', '/')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Your account is not active')
            else:
                # Check if user exists to give specific error
                try:
                    User.objects.get(email=email)
                    messages.error(request, 'Incorrect password')
                except User.DoesNotExist:
                    messages.error(request, 'No account found with this email')
                except Exception as e:
                    messages.error(request, f'Error checking user: {str(e)}')
        except Exception as e:
            import traceback
            error_msg = f'Authentication error: {str(e)}'
            messages.error(request, error_msg)
            print(f"Login Error: {error_msg}")
            traceback.print_exc()
        
        return render(request, 'accounts/login.html')

    return render(request, 'accounts/login.html')

@login_required(login_url='/accounts/login/')
def logout_view(request):
    logout(request)
    return render(request,'accounts/login.html')

def forgot_password(request):
    if request.method=="POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "User not found")
            return render(request,"accounts/forgot_password.html")
        token = str(uuid.uuid4())
        user.pwd_reset_token = token
        user.save()
        domain_name = request.headers['Origin']
        relative_path = reverse("reset_password",args=[token])
        url = f"{domain_name}{relative_path}"
        message = send_password_reset_email(url,user.email)
        if message:
            messages.success(request,"A verification code has been sent to your phone.")
        else:
            messages.error(request, "Something went wrong")
        return redirect("reset_password",user.id)
    
    return render(request,"accounts/forgot_password.html")

# Reset password view
def reset_password(request,token):
    try:
        user = User.objects.get(pwd_reset_token=token)
    except User.DoesNotExist:
        return redirect("forgot_password")
    
    if request.method=="POST":
        new_password = request.POST.get("password")
        confirm_password = request.POST.get("confirm-password")

        if user.pwd_reset_token != token:
            messages.error(request, "Verification code is incorrect.")
            return redirect("reset_password",token)
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("reset_password",token)
        
        user.set_password(new_password)
        user.pwd_reset_token = ""
        user.save()
        messages.success(request,"Your password has been changed.")
        return redirect("login")
    
    return render(request,"accounts/reset_password.html")