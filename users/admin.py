from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

class CustomUserAdmin(UserAdmin):
    # Display these fields in the admin panel
    list_display = ('username', 'email', 'role', 'block', 'created_by', 'created_at', 'last_updated_by', 'last_updated_at', 'is_staff', 'is_active')
    
    # Add filtering options
    list_filter = ('role', 'is_staff', 'is_active')

    # Fields to be displayed in the user edit form
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email', 'role', 'block', 'image')}),
        ('Tracking Info', {'fields': ('created_by', 'created_at', 'last_updated_by', 'last_updated_at')}),  # New Section
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fields for adding a new user (excluding created_by & last_updated_by)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'block', 'password1', 'password2'),
        }),
    )

    # Make `created_by` and `last_updated_by` read-only
    readonly_fields = ('created_by', 'created_at', 'last_updated_by', 'last_updated_at')

    search_fields = ('username', 'email')
    ordering = ('username',)

    def save_model(self, request, obj, form, change):
        """ Automatically set `created_by` and `last_updated_by`. """
        if not obj.pk:  # If the user is being created
            obj.created_by = request.user
        obj.last_updated_by = request.user  # Always update `last_updated_by`
        super().save_model(request, obj, form, change)

# Register User model with the custom admin
admin.site.register(User, CustomUserAdmin)

# Register Block and Farmer models
admin.site.register(Block)
admin.site.register(Farmer)


@admin.register(DailyFarmerCount)
class DailyFarmerCountAdmin(admin.ModelAdmin):
    list_display = ('surveyor', 'block', 'date', 'count')  # Columns in the admin panel
    list_filter = ('date', 'block')  # Filters for easy navigation
    search_fields = ('surveyor__username', 'block__name')  # Search by surveyor or block
    ordering = ('-date',) 



@admin.register(MonthlyFarmerReport)
class MonthlyFarmerReportAdmin(admin.ModelAdmin):
    list_display = ('surveyor', 'block', 'month', 'year', 'count')
    list_filter = ('month', 'year', 'block', 'surveyor')
    search_fields = ('surveyor__username', 'block__name')
