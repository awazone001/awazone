from django.db import models
from user_module.models import UserProfile
import secrets

class Sector(models.Model):
    id = models.CharField(max_length= 50,unique=True,primary_key=True)
    sector = models.CharField(max_length=50,verbose_name='Sector')
    description = models.TextField(verbose_name='Description')
    launch_date = models.DateTimeField(auto_now_add=True)
    is_available = models.BooleanField(verbose_name= 'Availability for Purchase')

    def __str__(self):
        return self.sector
    
    def save(self, *args, **kwargs):
        while not self.id:
            ref = secrets.token_urlsafe(10)
            object_with_similar_ref = Sector.objects.filter(id=ref)
            if not object_with_similar_ref:
                self.id = ref    
        super().save(*args, **kwargs)

class Asset(models.Model):
    id = models.CharField(max_length= 50,unique=True,primary_key=True)
    sector = models.ForeignKey(Sector,on_delete=models.CASCADE,null=True)
    asset = models.CharField(max_length=50,verbose_name= 'Asset')
    description  = models.TextField(verbose_name= 'Description')
    rate = models.DecimalField(verbose_name= 'Daily Rate',max_digits=14,decimal_places=2)
    minimum_purchase_amount = models.DecimalField(max_digits=14,decimal_places=2)
    minimum_duration = models.IntegerField(verbose_name= 'Duration before Sales(days)')
    maximum_duration = models.IntegerField(verbose_name= 'Duration before Expiration(days)')
    total_shares = models.DecimalField(verbose_name= 'Total Available Shares',max_digits=14,decimal_places=2)
    sold_out_volume = models.DecimalField(default=0,max_digits=14,decimal_places=2)
    percentage_bought = models.DecimalField(default=0,max_digits=14,decimal_places=2)
    share_rate = models.DecimalField(verbose_name= 'Fiat per Asset Shares',max_digits=14,decimal_places=2)
    launch_date = models.DateTimeField(auto_now_add=True)
    is_available = models.BooleanField(verbose_name= 'Availability for Purchase')

    class Meta:
        ordering = ('sector',)

    def __str__(self):
        return self.asset

    def save(self, *args, **kwargs):
        while not self.id:
            ref = secrets.token_urlsafe(10)
            object_with_similar_ref = Asset.objects.filter(id=ref)
            if not object_with_similar_ref:
                self.id = ref    
        super().save(*args, **kwargs)
  
class AssetPurchases(models.Model):
    user = models.ForeignKey(UserProfile,on_delete=models.CASCADE,null=True)
    id = models.CharField(primary_key=True,max_length=100)
    amount = models.DecimalField(max_digits=14,decimal_places=2,verbose_name='Enter Amount')
    sector = models.ForeignKey(Sector,on_delete=models.CASCADE,null=True)
    asset = models.ForeignKey(Asset,on_delete=models.CASCADE,null=True)
    share_value = models.DecimalField(max_digits=14,decimal_places=2)
    transaction_datetime = models.DateTimeField(auto_now_add=True)
    expiring_datetime = models.DateTimeField(auto_now_add=True)
    available_balance = models.DecimalField(max_digits=14,decimal_places=2,default=0)
    ledger_balance = models.DecimalField(max_digits=14,decimal_places=2,default=0)
    total_sale = models.DecimalField(max_digits=14,decimal_places=2,default=0)
    
    class Meta:
        ordering = ('-transaction_datetime',)

    def __str__(self):
        return self.id

class AssetSales(models.Model):
    user = models.ForeignKey(UserProfile,on_delete= models.CASCADE,null=True)
    purchase = models.ForeignKey(AssetPurchases,on_delete= models.CASCADE,null=True)
    id = models.CharField(primary_key=True,max_length=100)
    amount = models.DecimalField(max_digits=14,decimal_places=2,verbose_name='Enter Amount')
    share_value = models.FloatField()
    transaction_datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-transaction_datetime',)

    def __str__(self):
        return self.id
