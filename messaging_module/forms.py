from django.forms import CharField,Textarea,forms,ValidationError,PasswordInput

class ContactForm(forms.Form):
    subject = CharField(max_length=50)
    content = CharField(max_length=4000,required=True,widget = Textarea)
    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['subject'].label = "subject"
        self.fields['content'].label = "What do you want to say?"

class MailForm(forms.Form):
    subject = CharField(max_length=50)
    content = CharField(max_length=4000,required=True,widget = Textarea)

def only_int(value): 
        if value.isdigit()==False:
            raise ValidationError('Only accepts numbers')

class OTPForm(forms.Form):
    code = CharField(widget= PasswordInput(attrs={'placeholder': 'Enter OTP'}),max_length= 6,validators=[only_int],label='Enter OTP')