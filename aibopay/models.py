from django.db import models
import secrets
from user_module.models import UserProfile
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils import timezone
         
class AIBOWallet(models.Model):
    user = models.OneToOneField(UserProfile,on_delete=models.CASCADE,null=True)
    wallet_number = models.CharField(max_length=50,null=False,primary_key=True)
    pin = models.CharField(max_length =50 ,editable=True,null=True)
    balance = models.DecimalField(default=0,max_digits=14,decimal_places=2)
    inflow = models.DecimalField(default=0,max_digits=14,decimal_places=2)
    outflow = models.DecimalField(default=0,max_digits=14,decimal_places=2)

    def __str__(self):
        return self.wallet_number
    
    #wallet number algorithm
    def WalletID():
        ID = '01'
        for _ in range(10):
            num = str(secrets.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]))
            ID += num
        return int(ID)
        
    def create_wallet(user):
        try:
            # Create a new instance of AIBOWallet and associate it with the user
            wallet = AIBOWallet.objects.create(
                user=user,
                wallet_number = AIBOWallet.WalletID()
                )
            return wallet
        except Exception as e:
            # Handle any exceptions
            return None
    
class BankAccount(models.Model):
    wallet = models.ForeignKey(AIBOWallet, on_delete=models.CASCADE)
    bank_name = models.CharField(max_length=150)
    bank_id = models.CharField(max_length=10)
    bank_code = models.CharField(max_length=100)
    account_number = models.CharField(max_length=15)
    account_name = models.CharField(max_length=150)
    account_type = models.CharField(max_length=100,null=True)
    payout = models.IntegerField(null=True)
    verified = models.BooleanField(default=False)


    def create_account(bank_data, user_wallet):
        """Create a new bank account associated to an existing wallet."""
        if not isinstance(user_wallet, AIBOWallet):
            raise ValueError("First argument must be an instance of AIBOWallet")

        # Additional data validation can go here...

        # Use Django's built-in model creation functionality to save the new object
        # to the database. This will also automatically set the `user` field
        # since we defined it as a ForeignKey above.
        account = BankAccount(**bank_data, wallet=user_wallet)
        account.save()
        return account

class AIBORates(models.Model):
    arp_rate = models.DecimalField(default=0,max_digits=14,decimal_places=2,verbose_name='Fiat per ARP')
    monthly_subscription = models.DecimalField(max_digits=14,decimal_places=2,verbose_name='Monthly Subscription Amount')
    yearly_subscription = models.DecimalField(max_digits=14,decimal_places=2,verbose_name='Yearly Subscription Amount')
    charge_rate = models.DecimalField(max_digits=3,decimal_places=2,verbose_name='Percentage Charge per Transaction')
    created_at = models.DateTimeField(auto_now_add = True)

    def save(self, *args, **kwargs):
        if self.charge_rate > 100:
            raise ValidationError('Value cannot be greater than 100%')
        else:
            licenses_object = AIBORates.objects.filter()
            if not licenses_object.count():
                super().save(*args, **kwargs)    
            licenses_object.delete()
            super().save(*args, **kwargs)
    
    def update_rates(self,*args,**kwargs):
        previous_rates = AIBORates.objects.latest("created_at")
        previous_rates.arp_rate = self.arp_rate
        previous_rates.monthly_subscription = self.monthly_subscription
        previous_rates.yearly_subscription = self.yearly_subscription
        previous_rates.charge_rate = self.charge_rate
        previous_rates.save()

class WalletTransaction(models.Model):

    TRANSACTION_TYPES = (
        ('Deposit', 'Deposit'),
        ('Transfer', 'Transfer'),
        ('Withdraw', 'Withdraw'),
        ('Purchase', 'Purchase'),
    )

    transaction_status = (
        ("Pending", "Pending"),
        ("Success", "Success"),
        ("Failed", "Failed"),
    )
    wallet = models.ForeignKey(AIBOWallet, null=True, on_delete=models.CASCADE)
    transaction_type = models.CharField(
        max_length=200, null=True,  choices=TRANSACTION_TYPES)
    email = models.EmailField()
    description = models.CharField(max_length=50, null=True,blank=True)
    amount = models.DecimalField(max_digits=100, null=True, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add = True)
    status = models.CharField(
        max_length=20,null=False,default="Pending",choices=transaction_status
        )
    recipient = models.ForeignKey(BankAccount,null=True, on_delete=models.CASCADE)
    ref = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        ordering = ('-timestamp',)

    def __str__(self):
        return f"Payment: {self.ref}"

    def amount_value(self):
        rate = AIBORates.objects.latest('created_at')
        charge = Decimal((rate.charge_rate * Decimal(self.amount)) / Decimal(100))
        return int((Decimal(self.amount) + charge) * Decimal(100))
    
    def amount_int(self):
        return int(self.amount)
    
    def save(self, *args, **kwargs):
        while not self.ref:
            ref = secrets.token_urlsafe(10)
            object_with_similar_ref = WalletTransaction.objects.filter(ref=ref)
            if not object_with_similar_ref:
                self.ref = ref    

        super().save(*args, **kwargs)

class MonthlyLicense(models.Model):
    user = models.OneToOneField(UserProfile,on_delete=models.CASCADE,null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)

    def new_purchase(user):
        try:
            license = MonthlyLicense.objects.get(user=user)
            if not license.is_valid:
                # If the current license has expired, create a new one and invalidate it
                license.is_valid = True
                license.save()
                return True
            else:
                return False
        except MonthlyLicense.DoesNotExist:
            # If no license exists for the user, create a new one
            license = MonthlyLicense(user=user)
            license.save()
            return True

    def expired(user):
        latest = MonthlyLicense.objects.get(user = user)
        latest.is_valid = False
        latest.save()

class YearlyLicense(models.Model):
    user = models.OneToOneField(UserProfile,on_delete=models.CASCADE,null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)

    def new_purchase(user):
        try:
            license = YearlyLicense.objects.get(user=user)
            if not license.is_valid:
                # If the current license has expired, create a new one and invalidate it
                license.is_valid = True
                license.save()
                return True
            else:
                return False
        except YearlyLicense.DoesNotExist:
            # If no license exists for the user, create a new one
            license = YearlyLicense(user=user)
            license.save()
            return True

    def expired(user):
        latest = YearlyLicense.objects.get(user = user)
        latest.is_valid = False
        latest.save()