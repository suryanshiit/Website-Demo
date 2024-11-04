from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
from geeksforgeeks import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import authenticate, login, logout
from . tokens import generate_token

# Create your views here.
def home(request):
    return render(request, "authentication/index.html")
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .tokens import generate_token  # Ensure you have this utility
from django.contrib.sites.shortcuts import get_current_site

def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']
        
        if len(username) > 20:
            messages.error(request, "Username must be under 20 characters!")
            return redirect('home')
        
        if pass1 != pass2:
            messages.error(request, "Passwords didn't match!")
            return redirect('home')
        
        if not username.isalnum():
            messages.error(request, "Username must be alphanumeric!")
            return redirect('home')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken! Please choose another.")
            return render(request, "authentication/signup.html") 
        
        # Create the user
        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = True  # Set to inactive for email confirmation (if needed)
        myuser.save()

        messages.success(request, "Your account has been created successfully!")
        return redirect('signin')  # Redirect to signin page after successful signup
        
    return render(request, "authentication/signup.html")

def dashboard_view(request):
    if request.user.is_authenticated:
        return render(request, "authentication/dashboard.html")
    else:
        return redirect('login')  # Redirect to login if not authenticated
 # Redirect to login if not authenticated


def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']  # Change this to 'pass1' if you want to keep it consistent with the form

        user = authenticate(username=username, password=pass1)
        
        if user is not None:
            login(request, user)
            return render(request, "authentication/dashboard.html")
        else:
            messages.error(request, "Bad Credentials!!")
            return redirect('home')
    
    return render(request, "authentication/index.html")




def signout(request):
    logout(request)
    messages.success(request, "Logged Out Successfully!!")
    return redirect('home')