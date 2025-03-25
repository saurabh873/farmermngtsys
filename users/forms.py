from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Block, Farmer
from django.core.validators import RegexValidator

class LoginForm(AuthenticationForm):
    pass

class UserForm(forms.ModelForm):
    profile_image = forms.ImageField(required=False, label="Upload Profile Picture")

    class Meta:
        model = User
        fields = ['username', 'password', 'role', 'block', 'profile_image']  # Keeping essential fields
        widgets = {
            'password': forms.PasswordInput(),
        }

    def save(self, commit=True, admin_user=None):
        """Override save method to set created_by and last_updated_by."""
        user = super().save(commit=False)

        if not user.pk:  # If user is being created
            user.created_by = admin_user
        user.last_updated_by = admin_user

        if commit:
            user.save()
        return user
class BlockForm(forms.ModelForm):
    class Meta:
        model = Block
        fields = ['name']

class FarmerForm(forms.ModelForm):
    # Custom Aadhar Validator (same as the model, ensuring 12-digit numeric input)
    aadhar_validator = RegexValidator(
        regex=r'^\d{12}$',
        message="Aadhar number must be exactly 12 digits and contain only numbers.",
        code='invalid_aadhar'
    )

    aadhar_id = forms.CharField(
        max_length=12,
        validators=[aadhar_validator],  # Apply RegexValidator
        help_text="Enter a valid 12-digit Aadhar number"
    )

    image = forms.ImageField(required=False, label="Upload Farmer Image")
    aadhar_image = forms.ImageField(required=False, label="Upload Aadhar Image")

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

