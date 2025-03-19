from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from functools import wraps
from .models import Block, User, Farmer
from .forms import LoginForm, ProfileForm, UserForm, BlockForm, FarmerForm
import sys

def role_required(roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')  # Redirect to login if session expired

            user_role = getattr(request.user, 'role', None)
            if user_role not in roles:
                return HttpResponseForbidden("You do not have permission to access this page.")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if user:
            login(request, user)
              # 30 minutes session expiry
            return redirect('dashboard')
        else:
            print("login_view: Authentication failed", file=sys.stderr)
    
    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    user_role = getattr(request.user, 'role', None)
    if user_role == 'admin':
        return render(request, 'users/admin_dashboard.html')
    elif user_role == 'supervisor':
        return render(request, 'users/supervisor_dashboard.html')
    elif user_role == 'surveyor':
        return render(request, 'users/surveyor_dashboard.html')

    print("dashboard: No valid role found, logging out", file=sys.stderr)
    logout(request)
    return redirect('login')

@login_required
@role_required(['admin'])
def create_block(request):
    form = BlockForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('dashboard')
    return render(request, 'users/create_block.html', {'form': form})

from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import User
from .forms import UserForm
from django.contrib.auth.decorators import login_required

@login_required
@role_required(['admin'])
def create_or_edit_user(request, user_id=None):
    user = get_object_or_404(User, id=user_id) if user_id else None
    is_editing = user is not None
    form = UserForm(request.POST or None, request.FILES or None, instance=user)

    if is_editing:
        form.fields['password'].required = False  # Make password optional when editing
        form.fields['block'].label = "Change Block"  # Update label for clarity

    if request.method == 'POST' and form.is_valid():
        assigned_block = form.cleaned_data.get('block')
        role = form.cleaned_data.get('role')

        # Prevent duplicate supervisor block assignment
        if role == 'supervisor':
            existing_supervisor = User.objects.filter(role='supervisor', block=assigned_block)
            if user:
                existing_supervisor = existing_supervisor.exclude(id=user.id)
            if existing_supervisor.exists():
                messages.error(request, f"Block '{assigned_block}' is already assigned to another supervisor. Please choose a different block.")
                return render(request, 'users/create_user.html', {'form': form, 'user': user, 'is_editing': is_editing})

        user = form.save(commit=False)

        # If editing, allow password and image updates
        new_password = request.POST.get('password')
        if new_password:
            user.set_password(new_password)  # Update password only if provided

        if 'profile_image' in request.FILES:
            user.image = request.FILES['profile_image']  # Update profile image if uploaded

        user.save()
        messages.success(request, f"User '{user.username}' has been successfully {'updated' if is_editing else 'created'}.")
        return redirect('list_users')

    return render(request, 'users/create_user.html', {
        'form': form,
        'user': user,
        'is_editing': is_editing,
    })


@login_required
@role_required(['surveyor'])
def add_or_edit_farmer(request, farmer_id=None):
    if farmer_id:
        farmer = get_object_or_404(Farmer, id=farmer_id, added_by=request.user)
    else:
        farmer = None

    form = FarmerForm(request.POST or None, request.FILES or None, instance=farmer)  # Handle file uploads

    if request.method == 'POST' and form.is_valid():
        farmer = form.save(commit=False)

        # Ensure the farmer is assigned to the surveyor's block
        if request.user.block:
            farmer.block = request.user.block
        else:
            return render(request, 'users/add_farmer.html', {
                'form': form, 
                'error': 'No block assigned to your account.'
            })
        
        farmer.added_by = request.user

        # Save uploaded images (if provided)
        if 'image' in request.FILES:
            farmer.image = request.FILES['image']
        if 'aadhar_image' in request.FILES:
            farmer.aadhar_image = request.FILES['aadhar_image']

        farmer.save()
        return redirect('dashboard')

    return render(request, 'users/add_farmer.html', {'form': form, 'farmer': farmer})




@login_required
@role_required(['admin'])
def list_users(request):
    role_filter = request.GET.get('role', None)  # Get role filter from URL params
    block_filter = request.GET.get('block', None)  # Get block filter from URL params
    search_query = request.GET.get('search', '').strip().lower()
    
    users = User.objects.all().select_related('block')

    if role_filter:
        users = users.filter(role=role_filter)
    if block_filter:
        users = users.filter(block__id=block_filter)
    if search_query:
        users = users.filter(username__icontains=search_query)
    
    blocks = Block.objects.all()  # Fetch all blocks for dropdown filter
    
    return render(request, 'users/list_users.html', {
        'users': users,
        'blocks': blocks,
        'selected_role': role_filter,
        'selected_block': block_filter,
        'search_query': search_query,
    })



@login_required
@role_required(['admin'])
def delete_user(request, user_id):
    user = User.objects.get(id=user_id)
    if user.role != 'admin':  # Prevent deleting other admins
        user.delete()
    return redirect('list_users')

@login_required
@role_required(['supervisor'])
def list_surveyors(request):
    """Allow a supervisor to see only surveyors assigned to their block."""
    if not request.user.block:
        return HttpResponseForbidden("No block assigned to your account.")
    
    surveyors = User.objects.filter(role='surveyor', block=request.user.block)
    
    return render(request, 'users/surveyors_list.html', {
        'surveyors': surveyors
    })


@login_required
@role_required(['surveyor'])
def delete_farmer(request, farmer_id):
    """Allow a surveyor to delete a farmer only if the farmer belongs to their assigned block."""
    farmer = get_object_or_404(Farmer, id=farmer_id, block=request.user.block)
    farmer.delete()
    return redirect('list_farmers')

@login_required
@role_required(['surveyor'])
def list_farmers(request):
    farmers = Farmer.objects.filter(block=request.user.block)  # Only show farmers in the surveyor's block
    return render(request, 'users/list_farmers.html', {'farmers': farmers})


@login_required
def profile(request):
    user = request.user
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            # Handle password update
            new_password = form.cleaned_data.get('password')
            if new_password:
                user.set_password(new_password)
            
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=user)
    
    return render(request, 'users/profile.html', {'form': form, 'user': user})
