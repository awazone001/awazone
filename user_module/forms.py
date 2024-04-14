from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.forms import (
    EmailInput,PasswordInput,EmailField,CharField,forms,ModelForm
    )
from crispy_forms.helper import FormHelper,Layout
from crispy_forms.bootstrap import PrependedText

class CreateUserForm(UserCreationForm):

    class Meta:
        model = UserProfile
        fields = [
            'first_name','last_name','email','username','password1','password2','referral_code'
            ]

class LoginForm(forms.Form):
    email = EmailField(
        widget=EmailInput(),
        error_messages={
            'required': '',
        }
    )
    password = CharField(
        widget=PasswordInput(),
        error_messages={
            'required': '',
        }
    )

class UserUpdateForm(ModelForm):

    class Meta:
        model = UserProfile
        fields = [
            'phone_number',
            'profile_image', 
        ]
        
    def __init__(self, *args, **kwargs):
        dailing_code = kwargs.pop('dailing_code', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            PrependedText('image','x'),
            PrependedText('phone_number', text=dailing_code),
        )

class LevelForm(ModelForm):

    class Meta:
        model = Level
        fields = "__all__"