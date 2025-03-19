from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class Block(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class User(AbstractUser):  
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('supervisor', 'Supervisor'),
        ('surveyor', 'Surveyor'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    block = models.ForeignKey('Block', on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to='user_images/', null=True, blank=True)  # Image Upload Field

    # Custom related names to avoid conflicts
    groups = models.ManyToManyField(Group, related_name="custom_user_groups")
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions")

    def __str__(self):
        return f"{self.username} - {self.role}"

class Farmer(models.Model):
    name = models.CharField(max_length=100)
    aadhar_id = models.CharField(max_length=12, unique=True)
    block = models.ForeignKey(Block, on_delete=models.CASCADE)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='farmer_images/', null=True, blank=True)  # Farmer Profile Image
    aadhar_image = models.ImageField(upload_to='aadhar_images/', null=True, blank=True)  # Aadhar Image

    def __str__(self):
        return self.name

