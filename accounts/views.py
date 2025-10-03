from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError
from core.models import Staff
import re
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

def is_admin(user):
    return user.groups.filter(name='Admin').exists()


@csrf_protect
def signin(request):
    # Get the 'next' parameter from GET or POST
    next_url = request.POST.get('next') or request.GET.get('next', '')

    if request.method == 'POST':
        staff_id = request.POST.get('staff_id').lower()
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')

        # Set session expiry depending on "remember me"
        if remember_me:
            request.session.set_expiry(1209600)  # 2 weeks
        else:
            request.session.set_expiry(1200)  # 20 minutes

        try:
            user = User.objects.get(username__iexact=staff_id)
            user = authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            try:
                staff = Staff.objects.get(user=user)
                login(request, user)

                # Force password change if still defaulting to national_id
                if user.check_password(staff.national_id):
                    change_password_url = reverse('accounts:change_password')
                    if next_url:
                        change_password_url += f'?next={next_url}'
                    return redirect(change_password_url)

                messages.success(request, 'Successfully logged in!')

                # Determine default dashboard
                if staff.is_admin:
                    redirect_url = reverse('core:staff_list')  # Admin dashboard
                else:
                    if staff.employment_category == 'CASUAL':
                        redirect_url = reverse('core:casuals')  # Casual dashboard
                    elif staff.employment_category == 'LOCUM':
                        redirect_url = reverse('core:locumdash')  # Locum dashboard
                    else:
                        redirect_url = reverse('core:staff_list')  # Fallback
                        messages.warning(
                            request,
                            'No specific dashboard for your employment category.'
                        )

                # Debug info
                if next_url:
                    is_safe = url_has_allowed_host_and_scheme(
                        next_url,
                        allowed_hosts={request.get_host()},
                        require_https=request.is_secure()
                    )
                    print(f"next_url: {next_url}, is_safe: {is_safe}, host: {request.get_host()}, secure: {request.is_secure()}")

                # Redirect safely
                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure()
                ):
                    return redirect(next_url)
                else:
                    return redirect(redirect_url)

            except Staff.DoesNotExist:
                messages.error(request, 'Staff profile not found')
                return redirect('core:staff_list')  # fallback
        else:
            messages.error(request, 'Invalid Staff ID or password')

    # GET request or failed login → render template with next_url
    return render(request, 'sign-in.html', {'next_url': next_url})


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

@login_required
def profile(request):
    try:
        # Fetch the Staff object linked to the authenticated user
        staff = Staff.objects.get(user=request.user)
        context = {
            'user': request.user,
            'staff': staff,  # Pass the Staff object to access unique_id and other fields
        }
        return render(request, "profile.html", context)
    except Staff.DoesNotExist:
        # Handle case where the user has no associated Staff profile
        context = {
            'user': request.user,
            'error': 'No staff profile found for this user.'
        }
        return render(request, "profile.html", context)