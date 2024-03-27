from django.forms import (
    ModelForm,forms,CharField,PasswordInput,ValidationError
    )
from .models import AIBORates,WalletTransaction
    
def only_int(value): 
        if value.isdigit()==False:
            raise ValidationError('Only accepts numbers')

class ResetPINForm(forms.Form):
    pin = CharField(widget= PasswordInput(attrs={'placeholder': 'Enter PIN'}),max_length= 4,validators=[only_int])
    confirm_pin = CharField(widget= PasswordInput(attrs={'placeholder': 'Confirm PIN'}),max_length= 4,validators=[only_int])

class DepositForm(ModelForm):

    class Meta:
        model = WalletTransaction
        fields=['amount','description']
    
class WithdrawalForm(ModelForm):

    class Meta:
        model = WalletTransaction
        fields = ['amount','description']

class VerifyAccountForm(forms.Form):
    account_number = CharField(max_length=11,validators=[only_int])

class AIBORatesForm(ModelForm):

    class Meta:
        model = AIBORates
        fields = "__all__"

class PINVerificationForm(forms.Form):
    pin = CharField(widget= PasswordInput(attrs={'placeholder': 'Enter PIN'}),max_length= 4,validators=[only_int])