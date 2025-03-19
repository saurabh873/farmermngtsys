from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import*  # Import your models

class CustomUserAdmin(UserAdmin):
    # Display these fields in the admin panel
    list_display = ('username', 'email', 'role', 'block', 'is_staff', 'is_active')
    
    # Add filtering options
    list_filter = ('role', 'is_staff', 'is_active')

    # Fields to be displayed in the user edit form
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email', 'role', 'block')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fields for adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'block', 'password1', 'password2'),
        }),
    )

    search_fields = ('username', 'email')
    ordering = ('username',)

# Register User model with the custom admin
admin.site.register(User, CustomUserAdmin)

# Register Block model
admin.site.register(Block)
admin.site.register(Farmer)
