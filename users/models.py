from django import forms
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.core.validators import RegexValidator
from django.utils.timezone import now

from farmermngt import settings

class Block(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.conf import settings

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('supervisor', 'Supervisor'),
        ('surveyor', 'Surveyor'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    block = models.ForeignKey('Block', on_delete=models.SET_NULL, null=True, blank=True)

    image = models.ImageField(upload_to='user_images/', null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_users"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="updated_users"
    )
    last_updated_at = models.DateTimeField(auto_now=True)

    groups = models.ManyToManyField(Group, related_name="custom_user_groups")
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['block'], condition=models.Q(role='supervisor'), name="unique_supervisor_per_block"),
        ]

    def __str__(self):
        return f"{self.username} - {self.role}"


class Farmer(models.Model):
    # Validator for 12-digit numeric Aadhar ID
    aadhar_validator = RegexValidator(
        regex=r'^\d{12}$',  # Ensures exactly 12 digits (only numbers)
        message="Aadhar number must be exactly 12 digits and contain only numbers.",
        code='invalid_aadhar'
    )

    name = models.CharField(max_length=100)
    aadhar_id = models.CharField(
        max_length=12,
        unique=True,  # Ensures uniqueness in the database
        validators=[aadhar_validator],  # Apply RegexValidator
        help_text="Enter a valid 12-digit Aadhar number"
    )
    block = models.ForeignKey(Block, on_delete=models.CASCADE)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='farmer_images/', null=True, blank=True,default='media/aadhar_images/NSCC_uwKVfC9.png')  # Farmer Profile Image
    aadhar_image = models.ImageField(upload_to='aadhar_images/', null=True, blank=True,default='media/aadhar_images/NSCC_uwKVfC9.png') 
    created_at = models.DateTimeField(default=now) # Aadhar Image

    def __str__(self):
        return self.name
    
class ProfileForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter new password'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'image'] 



class DailyFarmerCount(models.Model):
    surveyor = models.ForeignKey(User, on_delete=models.CASCADE)
    block = models.ForeignKey(Block, on_delete=models.CASCADE)
    date = models.DateField(default=now) 
    count = models.IntegerField(default=0)

    class Meta:
        unique_together = ('surveyor', 'date')  # Ensure one record per surveyor per day

    def __str__(self):
        return f"{self.surveyor.username} - {self.date} - {self.count} farmers"
# Ensure unique combination of user, block, and date


class MonthlyFarmerReport(models.Model):
    surveyor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'surveyor'})
    block = models.ForeignKey(Block, on_delete=models.CASCADE)  
    month = models.IntegerField()  # 1 (Jan) to 12 (Dec)
    year = models.IntegerField()
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('surveyor', 'block', 'month', 'year')  # Ensure no duplicate entries

    def __str__(self):
        return f"{self.surveyor.username} - {self.block.name} - {self.month}/{self.year} - {self.count} Farmers"