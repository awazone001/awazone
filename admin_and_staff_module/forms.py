from django.forms import ModelForm
from .models import SlidePhoto,TermsAndConditions
class SlidePhotoForm(ModelForm):

    class Meta:
        model = SlidePhoto
        fields=['image','description']

class TermsAndConditionsForms(ModelForm):

    class Meta:
        model = TermsAndConditions
        exclude = ['date_created','last_updated']