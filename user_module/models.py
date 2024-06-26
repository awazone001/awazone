from django.db import models
from django.contrib.auth.models import AbstractUser,UserManager
from django.db import transaction
from PIL import Image
import secrets
import requests
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.exceptions import ValidationError

def get_dialing_code(country_code):

    url = 'http://country.io/phone.json'
    response = requests.get(url)

    if response.status_code == 200:
        content = response.json()
        return content[country_code]
    else:
        return None
        
class UserProfile(AbstractUser):
    first_name = models.CharField(max_length=50,blank=False,verbose_name='First name')
    last_name = models.CharField(max_length=50,blank=False,verbose_name='Last name')
    username = models.CharField(max_length=50,unique=True,verbose_name='Username')
    email = models.EmailField(unique = True,verbose_name='Email')
    profile_image = models.ImageField(upload_to='profile_pictures/',verbose_name='Profile Picture')
    phone_number = models.CharField(max_length = 11)
    is_active = models.BooleanField(default=False,verbose_name= 'Account active')
    is_staff = models.BooleanField(default = False,verbose_name='Staff')
    user_code = models.CharField(max_length=200,unique= True,null=True)
    referral_code = models.CharField(max_length=200,blank = True,null=True)
    team = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add = True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self):
        return self.email
    
    #referral code generator using user email 
    def generate_ref(self, email):
        number_code = ''
        for _ in range(5):
            number = str(secrets.choice([0,1,2,3,4,5,6,7,8,9]))
            number_code += number
        return email.split('@')[0] + number_code

    #check if referral code exist
    def referral_clean(self,ref_code):
        try:
            UserProfile.objects.get(user_code = ref_code)
            return True
        except UserProfile.DoesNotExist:
            return False

    def save(self, *args, **kwargs):
        if self.referral_code:
            if not self.referral_clean(self.referral_code):
                self.referral_code = None

        self.first_name = self.first_name.capitalize()
        self.last_name = self.last_name.capitalize()
        if self.user_code is None:
            self.user_code = self.generate_ref(self.email)

        if not self.profile_image:
            # Set a default profile image
            default_image_path = settings.STATIC_ROOT + '/images/avatar.jpg'
            with open(default_image_path, 'rb') as f:
                default_image_data = f.read()
            self.profile_image.save('default_avatar.jpg', ContentFile(default_image_data), save=True)

        # Process image if provided
        if self.profile_image:
            img = Image.open(self.profile_image)
            if img.height > 100 or img.width > 100:
                img.thumbnail((100, 100))
                img_buffer = BytesIO()
                img.save(img_buffer, format='JPEG')
                img_buffer.seek(0)
                self.profile_image.save(self.profile_image.name, ContentFile(img_buffer.read()), save=True)

        super().save(*args, **kwargs)

    def activate(self):
        try:
            self.is_active =True
            self.save()
        except Exception as e:
            return f"Error Occurred: {e}"
        
    def deactivate(self):
        try:
            self.is_active=False
            self.save()
        except Exception as e:
            return f"Error Occurred: {e}"
        
    #create new user
    def create_aibo(self):
        try:
            with transaction.atomic():
                aibo  = AIBO.objects.create(
                    user = self
                )
                aibo.save()
                return True
        except Exception as e:
            print(e)
            raise ValidationError("User creation failed")

    #create new staff
    def create_staff(self):
        try:
            self.is_staff=True
            self.save()
            return True
        except Exception as e:
            return f"Error Occurred: {e}"
        
    def unmake_staff(self):
        try:
            self.is_staff=False
            self.save()
            return True
        except Exception as e:
            return f"Error Occurred: {e}"
    
    #create new admin
    def create_admin(self):
        try:
            self.is_staff=True
            self.is_superuser = True
            self.save()
            return True
        except  Exception as e:
            return f"Error Occurred: {e}"

class Level(models.Model):
    LEVEL_CHOICES = (
        ('Level 1', 'Level 1'),
        ('Level 2', 'Level 2'),
        ('Level 3', 'Level 3'),
        ('Level 4', 'Level 4'),
        ('Level 5', 'Level 5'),
        ('Level 6', 'Level 6'),
        ('Level 7', 'Level 7'),
        ('Level 8', 'Level 8'),
        ('Level 9', 'Level 9'),
        ('Level 10', 'Level 10')
    )

    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, primary_key=True, verbose_name='Level')
    title = models.CharField(max_length=100, verbose_name='Rank')
    description = models.TextField(verbose_name='Description')
    direct_team = models.IntegerField(verbose_name='Direct Team Size')
    number_team = models.IntegerField(verbose_name='Total Team Size')
    user_reward = models.TextField(verbose_name='User Reward')
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def get_default_level(cls):
        # You can customize this method to return the desired default level
        return Level.objects.get(level="Level 1")
    class Meta:
        ordering = ('level',)

    def __str__(self):
        return self.title
    
class AIBO(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    arp = models.FloatField(default=0)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, null=True, blank=True)
    auto_renew_license = models.BooleanField(default=False, verbose_name='Auto Renew Licenses and Subscription')
    is_valid_for_monthly_license = models.BooleanField(default=True)
    is_valid_for_yearly_license = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user)  # Make sure to return a string

    def save(self, *args, **kwargs):
        if not self.level:
            # Retrieve the default level object
            default_level = Level.get_default_level()
            self.level = default_level
        
        super().save(*args, **kwargs)
