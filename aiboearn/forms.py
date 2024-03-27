from django.forms import ModelForm
from .models import Sector,Asset,AssetPurchases,AssetSales

class AssetPurchaseForm(ModelForm):

    class Meta:
        model = AssetPurchases
        fields = ['sector','asset','amount']

class AssetSaleForm(ModelForm):

    class Meta:
        model = AssetSales
        fields = ['amount',]

class SectorForm(ModelForm):

    class Meta:
        model = Sector
        exclude = ['id','launch_date']

class AssetForm(ModelForm):

    class Meta:
        model = Asset
        exclude = ['id','sold_out_volume','percentage_bought','launch_date',]