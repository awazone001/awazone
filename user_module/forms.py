from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.forms import forms, ModelForm
from django import forms
from crispy_forms.helper import FormHelper,Layout
from crispy_forms.bootstrap import PrependedText
from django.core.exceptions import ValidationError
from crispy_forms.layout import Layout, Field

class CreateUserForm(UserCreationForm):
    class Meta:
        model = UserProfile
        fields = [
            'first_name','last_name','email','username','password1','password2','referral_code'
            ]

class LoginForm(forms.Form):
    username_or_email = forms.CharField(
        max_length=254,
        widget=forms.TextInput(),
        error_messages={
            'required': 'Please enter your username or email.',
        }
    )
    password = forms.CharField(
        widget=forms.PasswordInput(),
        error_messages={
            'required': 'Please enter your password.',
        }
    )

    def clean(self):
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get('username_or_email')
        password = cleaned_data.get('password')

        if username_or_email and password:
            # Check if input is an email
            if '@' not in username_or_email:
                try:
                    user = UserProfile.objects.get(username=username_or_email)
                    cleaned_data['username_or_email'] = user.email
                except UserProfile.DoesNotExist:
                    raise ValidationError("User with this username does not exist.")
            else:
                cleaned_data['username_or_email'] = username_or_email


            return cleaned_data
            
        else:
            raise ValidationError("Please provide both username/email and password.")
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'phone_number',
            'profile_image', 
        ]

class LevelForm(ModelForm):

    class Meta:
        model = Level
        fields = "__all__"