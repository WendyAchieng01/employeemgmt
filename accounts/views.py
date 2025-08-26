from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError
from core.models import Staff
import re

def is_admin(user):
    return user.groups.filter(name='Admin').exists()

def signin(request):
    if request.method == 'POST':
        staff_id = request.POST.get('staff_id').lower()  
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')

        try:
            user = User.objects.get(username__iexact=staff_id)
            user = authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            try:
                staff = Staff.objects.get(user=user)
                login(request, user)
                # Set session expiry to 20 minutes (1200 seconds) for inactivity logout
                request.session.set_expiry(1200)
                
                if user.check_password(staff.national_id):
                    return redirect('accounts:change_password')
                
                messages.success(request, 'Successfully logged in!')
                return redirect('core:staff_list')  
            except Staff.DoesNotExist:
                messages.error(request, 'Staff profile not found')
        else:
            messages.error(request, 'Invalid Staff ID or password')

    return render(request, 'sign-in.html')

def signup(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        staff_id = request.POST.get('staff_id').lower()  
        password = request.POST.get('password')
        terms_agreed = request.POST.get('terms')

        if not terms_agreed:
            messages.error(request, 'You must agree to the Terms and Conditions')
            return render(request, 'sign-up.html')

        if User.objects.filter(username__iexact=staff_id).exists():
            messages.error(request, 'Staff ID already exists')
            return render(request, 'sign-up.html')

        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
            return render(request, 'sign-up.html')

        try:
            user = User.objects.create_user(
                username=staff_id,
                password=password,
                first_name=name
            )
            user.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('accounts:signin')
        except ValidationError as e:
            messages.error(request, str(e))
    
    return render(request, 'sign-up.html')

def signout(request):
    logout(request)
    messages.success(request, 'Successfully logged out!')
    return redirect('accounts:signin')

def change_password(request):
    if not request.user.is_authenticated:
        return redirect('accounts:signin')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'change-password.html')

        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
            return render(request, 'change-password.html')

        try:
            user = request.user
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Password updated successfully! Please log in again.')
            logout(request)
            return redirect('accounts:signin')
        except Exception as e:
            messages.error(request, f'Error updating password: {str(e)}')

    return render(request, 'change-password.html')