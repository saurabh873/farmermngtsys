import csv
from datetime import datetime
import json
from time import localtime
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from functools import wraps
from django.utils.timezone import now
import redis
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import MonthlyFarmerReport, User
from .forms import *
from django.contrib.auth.decorators import login_required
from farmermngt import settings
from .models import Block, DailyFarmerCount, User, Farmer
from .tasks import store_and_reset_farmer_counts
from django.utils.dateparse import parse_date
import sys
from rest_framework import viewsets, permissions
from .models import Farmer
from .serializers import FarmerSerializer
from django.middleware.csrf import get_token
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from .models import Farmer, Block, User
from .serializers import FarmerSerializer

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


import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.middleware.csrf import get_token

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.middleware.csrf import get_token
from django.http import JsonResponse
from django.shortcuts import render, redirect
import json

def login_view(request):
    form = AuthenticationForm()  # Django's built-in login form

    if request.method == "GET":
        if request.headers.get("Accept") == "application/json":
            csrf_token = get_token(request)
            return JsonResponse({"csrf_token": csrf_token})

        return render(request, "users/login.html", {"form": form})

    if request.method == "POST":
        if request.content_type == "application/json":
            try:
                data = json.loads(request.body.decode("utf-8"))
                username = data.get("username")
                password = data.get("password")
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON"}, status=400)
        else:
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data["username"]
                password = form.cleaned_data["password"]
            else:
                return render(request, "users/login.html", {"form": form})

        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            if request.content_type == "application/json":
                return JsonResponse({"message": "Login successful"}, status=200)
            return redirect("dashboard")

        form.add_error(None, "Invalid credentials")
        return render(request, "users/login.html", {"form": form})

    return JsonResponse({"error": "Method not allowed"}, status=405)



@login_required
def logout_view(request):
    logout(request)
    return redirect('login')



@login_required
def dashboard(request):
    """ Show dashboard based on user role """

    current_date = now().date()  # Fix: Correctly fetch current date
    current_month = current_date.month
    current_year = current_date.year

    if request.user.role == "surveyor":
        # 🔹 Fetch real-time counts
        user_redis_key = f"user_{request.user.id}_farmer_count"
        my_daily_count = int(redis_client.get(user_redis_key) or 0)

        total_redis_key = "total_farmers_today"
        total_farmers_today = int(redis_client.get(total_redis_key) or 0)

        return render(request, 'users/surveyor_dashboard.html', {
            'my_daily_count': my_daily_count,
            'total_farmers_today': total_farmers_today,
        })

    elif request.user.role == "admin":
        total_farmers_today = int(redis_client.get("total_farmers_today") or 0)

        # 🔹 Fetch all surveyors and their farmer counts from Redis
        surveyors = User.objects.filter(role="surveyor")
        surveyor_counts = {
            s.id: int(redis_client.get(f"user_{s.id}_farmer_count") or 0) for s in surveyors
        }

        # 🔹 Fetch current month reports
        monthly_reports = MonthlyFarmerReport.objects.filter(month=current_month, year=current_year)

        return render(request, 'users/admin_dashboard.html', {
            'total_farmers_today': total_farmers_today,
            'surveyor_counts': surveyor_counts,
            'monthly_reports': monthly_reports,  
        })

    elif request.user.role == "supervisor":
        # 🔹 Fetch real-time farmer count for the assigned block
        assigned_block = request.user.block
        block_farmers_count = Farmer.objects.filter(block=assigned_block).count()
        
        # 🔹 Fetch surveyors under the supervisor’s block
        surveyors = User.objects.filter(role='surveyor', block=assigned_block)

        return render(request, 'users/supervisor_dashboard.html', {
            'block_farmers_count': block_farmers_count,
            'surveyors': surveyors  # ✅ Include surveyors list
        })

    else:
        messages.error(request, "Unauthorized access.")
        return redirect('login')




@login_required
@role_required(['admin'])
def create_block(request):
    form = BlockForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('dashboard')
    return render(request, 'users/create_block.html', {'form': form})



@login_required
@role_required(['admin'])
def create_user(request):
    """Admin can create a new user: Supervisor, Surveyor, or another Admin."""
    if request.user.role != 'admin':  # Only admins can create users
        messages.error(request, "You don't have permission to create users.")
        return redirect('dashboard')

    form = UserForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        role = form.cleaned_data['role']
        assigned_block = form.cleaned_data.get('block')

        # Supervisor Validation: Ensure unique block assignment
        if role == 'supervisor' and User.objects.filter(role='supervisor', block=assigned_block).exists():
            messages.error(request, f"Block '{assigned_block}' already has a supervisor. Choose a different block.")
            return render(request, 'users/create_user.html', {'form': form})

        # Surveyor Validation: Ensure they are assigned to a supervisor in the same block
        if role == 'surveyor':
            supervisor = User.objects.filter(role='supervisor', block=assigned_block).first()
            if not supervisor:
                messages.error(request, "No supervisor exists for the selected block. Create a supervisor first.")
                return render(request, 'users/create_user.html', {'form': form})

        user = form.save(commit=False)
        user.created_by = request.user  # Track creator
        user.last_updated_by = request.user  # Track last update
        user.set_password(form.cleaned_data['password'])  # Hash password

        # Assign block from supervisor for surveyors
        if role == 'surveyor':
            user.block = supervisor.block  # Inherit block from supervisor

        user.save()
        
        messages.success(request, f"User '{user.username}' has been successfully created.")
        return redirect('dashboard')

    return render(request, 'users/create_user.html', {'form': form})


@login_required
@role_required(['admin'])
def update_user(request, user_id):
    """Admin can update an existing user."""
    user = get_object_or_404(User, id=user_id)
    form = UserForm(request.POST or None, request.FILES or None, instance=user)

    # Make password optional when editing
    form.fields['password'].required = False
    form.fields['block'].label = "Change Block"

    if request.method == 'POST' and form.is_valid():
        assigned_block = form.cleaned_data.get('block')
        role = form.cleaned_data.get('role')

        # Prevent duplicate supervisor block assignment
        if role == 'supervisor':
            existing_supervisor = User.objects.filter(role='supervisor', block=assigned_block).exclude(id=user.id)
            if existing_supervisor.exists():
                messages.error(request, f"Block '{assigned_block}' is already assigned to another supervisor.")
                return render(request, 'users/update_user.html', {'form': form, 'user': user})

        updated_user = form.save(commit=False)
        updated_user.last_updated_by = request.user  # Track who last updated
        new_password = request.POST.get('password')

        if new_password:
            updated_user.set_password(new_password)  # Update password if provided

        if 'profile_image' in request.FILES:
            updated_user.image = request.FILES['profile_image']  # Update profile image if uploaded

        updated_user.save()
        messages.success(request, f"User '{updated_user.username}' has been successfully updated.")
        return redirect('list_users')

    return render(request, 'users/update_user.html', {'form': form, 'user': user})



redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)


# Initialize Redis


@login_required
@role_required(['surveyor'])
def add_farmer(request):
    """ View to add a farmer and update Redis-based tracking. """
    
    form = FarmerForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        farmer = form.save(commit=False)
        surveyor = request.user

        if not surveyor.block:
            messages.error(request, "Error! No block assigned to your account.")
            return render(request, 'users/add_farmer.html', {'form': form})

        farmer.block = surveyor.block
        farmer.added_by = surveyor
        farmer.save()

        # 🔹 Redis Keys
        surveyor_key = f"surveyor:{surveyor.id}:daily_farmer_count"
        block_key = f"block:{surveyor.block.id}:daily_farmer_count"

        # 🔹 Update Redis Atomically
        with redis_client.pipeline() as pipe:
            pipe.incr(surveyor_key)  # Surveyor's count
            pipe.incr(block_key)  # Block's total count

            # ✅ Set expiry at midnight dynamically
            seconds_until_midnight = (now().replace(hour=23, minute=59, second=59) - now()).seconds
            pipe.expire(surveyor_key, seconds_until_midnight)
            pipe.expire(block_key, seconds_until_midnight)

            pipe.execute()  # Execute atomic Redis operations

        messages.success(request, "Farmer added successfully!")
        return redirect('dashboard')

    return render(request, 'users/add_farmer.html', {'form': form})



@login_required
@role_required(['surveyor'])
def get_real_time_counts(request):
    """ Fetch real-time farmer count for surveyor & block from Redis """
    surveyor = request.user

    if not surveyor.block:
        return JsonResponse({'error': 'No block assigned'}, status=400)

    # 🔹 Redis Keys
    surveyor_key = f"surveyor:{surveyor.id}:daily_farmer_count"
    block_key = f"block:{surveyor.block.id}:daily_farmer_count"

    # 🔹 Fetch Counts
    my_count = int(redis_client.get(surveyor_key) or 0)
    block_count = int(redis_client.get(block_key) or 0)

    return JsonResponse({
        'my_count': my_count,
        'block_count': block_count
    })





@login_required
@role_required(['surveyor'])
def edit_farmer(request, farmer_id):
    """ View to edit an existing farmer """
    
    farmer = get_object_or_404(Farmer, id=farmer_id, added_by=request.user)
    form = FarmerForm(request.POST or None, request.FILES or None, instance=farmer)

    if request.method == 'POST':
        if form.is_valid():
            farmer = form.save(commit=False)
            farmer.save()
            messages.success(request, "Farmer updated successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Error! Please check the form fields.")

    return render(request, 'users/edit_farmer.html', {'form': form, 'farmer': farmer})




@login_required
@role_required(['admin'])
def list_users(request):
    # Get filters from request
    search_query = request.GET.get('search', '').strip().lower()
    
    # Get multi-select values (comma-separated in URL)
    role_filter = request.GET.get('role', '')
    block_filter = request.GET.get('block', '')

    # Convert comma-separated values into lists
    selected_roles = role_filter.split(',') if role_filter else []
    selected_blocks = block_filter.split(',') if block_filter else []

    # Fetch all users
    users = User.objects.all().select_related('block')

    # Apply search filter
    if search_query:
        users = users.filter(username__icontains=search_query)

    # Apply role filter (if multiple roles selected)
    if selected_roles:
        users = users.filter(role__in=selected_roles)

    # Apply block filter (if multiple blocks selected)
    if selected_blocks:
        users = users.filter(block_id__in=selected_blocks)

    # Fetch all blocks for dropdown
    blocks = Block.objects.all()

    return render(request, 'users/list_users.html', {
        'users': users,
        'blocks': blocks,
        'selected_roles': selected_roles,
        'selected_blocks': selected_blocks,
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


redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
@login_required
def delete_farmer(request, farmer_id):
    farmer = get_object_or_404(Farmer, id=farmer_id)

    # Get surveyor and block details before deletion
    surveyor = farmer.added_by
    block = farmer.block

    if request.user != surveyor:  # Ensure only the surveyor can delete their own farmers
        messages.error(request, "You are not allowed to delete this farmer.")
        return redirect('list_farmers')

    # Delete farmer from the database
    farmer.delete()

    # 🔹 Decrement the count in Redis
    surveyor_key = f"surveyor:{surveyor.id}:daily_farmer_count"
    block_key = f"block:{block.id}:daily_farmer_count"

    if redis_client.exists(surveyor_key):
        redis_client.decr(surveyor_key)  # Decrement the surveyor's count

    if redis_client.exists(block_key):
        redis_client.decr(block_key)  # Decrement the block's count

    messages.success(request, "Farmer deleted successfully.")
    return redirect('list_farmers')
@login_required
@role_required(['surveyor'])
def list_farmers(request):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    farmers = Farmer.objects.filter(block=request.user.block).select_related("block", "added_by")

    if start_date and end_date:
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)

        if start_date and end_date:
            farmers = farmers.filter(created_at__date__range=(start_date, end_date))

    # If CSV export requested
    if request.GET.get("export") == "1":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="farmers_{start_date}_{end_date}.csv"'

        writer = csv.writer(response)
        writer.writerow(["Name", "Aadhaar Number", "Block", "Added By", "Created At"])

        for farmer in farmers:
            writer.writerow([farmer.name, farmer.aadhar_id, farmer.block.name, farmer.added_by.username, farmer.created_at])

        return response

    return render(request, "users/list_farmers.html", {"farmers": farmers, "start_date": start_date, "end_date": end_date})


@login_required
def profile(request):
    user = request.user

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            new_password = form.cleaned_data.get('password')

            if new_password:
                user.set_password(new_password)  # Hashes and sets the new password
                user.save()  # Ensure password update is saved properly

                logout(request)  # Log out user after password change
                messages.success(request, 'Password changed successfully. Please log in again.')
                return redirect('login')  # Redirect to login page
            
            else:
                # Explicitly update other fields manually
                user.first_name = form.cleaned_data.get('first_name', user.first_name)
                user.last_name = form.cleaned_data.get('last_name', user.last_name)
                user.email = form.cleaned_data.get('email', user.email)
                user.image = form.cleaned_data.get('image', user.image)  # Ensure image updates
                user.save()  # Save user changes
                
                messages.success(request, 'Profile updated successfully.')
                return redirect('dashboard')  # Redirect to dashboard after update

    else:
        form = ProfileForm(instance=user)

    return render(request, 'users/profile.html', {'form': form, 'user': user})






@login_required
@role_required(['surveyor'])
def get_real_time_counts(request):
    """ Fetch real-time farmer count for surveyor & block from Redis """
    surveyor = request.user

    if not surveyor.block:
        return JsonResponse({'error': 'No block assigned'}, status=400)

    # 🔹 Redis Keys
    surveyor_key = f"surveyor:{surveyor.id}:daily_farmer_count"
    block_key = f"block:{surveyor.block.id}:daily_farmer_count"

    # 🔹 Fetch Counts
    my_count = int(redis_client.get(surveyor_key) or 0)
    block_count = int(redis_client.get(block_key) or 0)

    return JsonResponse({
        'my_count': my_count,
        'block_count': block_count
    })








from rest_framework import status



@method_decorator(login_required, name='dispatch')
class FarmerView(APIView):
    """
    API to handle both:
    - Creating a farmer (POST) - Only Surveyors can add farmers.
    - Listing farmers (GET) - Admins, Supervisors, and Surveyors can view farmers.
    """

    def get(self, request, *args, **kwargs):
        """Handles fetching farmers based on user role."""
        user = request.user

        if user.role == "admin":
            farmers = Farmer.objects.all()
        elif user.role == "supervisor":
            farmers = Farmer.objects.filter(block=user.block)
        elif user.role == "surveyor":
            farmers = Farmer.objects.filter(added_by=user)
        else:
            return Response({"error": "Unauthorized access"}, status=status.HTTP_403_FORBIDDEN)

        serializer = FarmerSerializer(farmers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Handles creating a new farmer (only for surveyors)."""
        if request.user.role != "surveyor":
            raise PermissionDenied("Only surveyors can add farmers.")

        assigned_block = request.user.block
        if not assigned_block:
            return Response({"error": "Surveyor is not assigned to any block."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = FarmerSerializer(data=request.data)
        if serializer.is_valid():
            aadhar_id = serializer.validated_data.get('aadhar_id')
            if Farmer.objects.filter(aadhar_id=aadhar_id).exists():
                return Response({"error": "A farmer with this Aadhar ID already exists."}, status=status.HTTP_400_BAD_REQUEST)

            farmer = serializer.save(added_by=request.user, block=assigned_block)
            return Response(FarmerSerializer(farmer).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

