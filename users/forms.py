from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Block, Farmer

class LoginForm(AuthenticationForm):
    pass

class UserForm(forms.ModelForm):
    profile_image = forms.ImageField(required=False, label="Upload Profile Picture")  # New Image Field

    class Meta:
        model = User
        fields = ['username', 'password', 'role', 'block', 'profile_image']  # Added profile_image
        widgets = {
            'password': forms.PasswordInput()
        }
class BlockForm(forms.ModelForm):
    class Meta:
        model = Block
        fields = ['name']

class FarmerForm(forms.ModelForm):
    image = forms.ImageField(required=False, label="Upload Farmer Image")  
    aadhar_image = forms.ImageField(required=False, label="Upload Aadhar Image")  # Added Aadhar Image Field  

    class Meta:
        model = Farmer
        fields = ['name', 'aadhar_id', 'image', 'aadhar_image'] 


class ProfileForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False, label='New Password')
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'password', 'image', 'role', 'block']
        widgets = {
            'role': forms.TextInput(attrs={'readonly': 'readonly'}),
            'block': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

