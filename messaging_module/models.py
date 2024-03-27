from django.db import models
import secrets
from user_module.models import UserProfile
import secrets
from datetime import datetime, timedelta
from .mailing import send_otp_email

class Notification(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE,related_name='notifications_to')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE,null=True,related_name='notifications_from')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.message
    
    def create_notification(user, message,*args,**kwargs):
        notification = Notification(user=user, message=message)
        notification.save()

    def notify_all_users(message):
        all_users = UserProfile.objects.filter(is_user = True)
        for users in all_users:
            Notification.create_notification(user = users,message=message)

    def notify_all_staff(message,sender,*args,**kwargs):
        all_users = UserProfile.objects.filter(is_staff = True)
        for users in all_users:
            Notification.create_notification(user = users,message=message,sender=sender)

    def mark_as_read(self):
        self.is_read = True
        self.save()

class ChatRoom(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    is_lock = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ('-timestamp',)
    
    def save(self, *args, **kwargs):
        while not self.name:
            ref = secrets.token_urlsafe(10)
            object_with_similar_ref = ChatRoom.objects.filter(name=ref)
            if not object_with_similar_ref:
                self.name = ref    

        super().save(*args, **kwargs)
        return self.name

class ChatMessage(models.Model):
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.sender.username} - {self.timestamp}'
    
class Contact(models.Model):
    user = models.EmailField()
    subject = models.CharField(max_length=100)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class OTP(models.Model):
    ref = models.CharField(max_length=100,unique=True,null=True)
    user = models.ForeignKey(UserProfile,on_delete=models.CASCADE)
    code = models.CharField(max_length=6,verbose_name='Enter OTP')
    timestamp = models.DateTimeField(auto_now_add=True)
    expired = models.BooleanField(default=False)        

    def isValidCode(self, code):
        if self.code == code:
            delta = timedelta(minutes=5)  # 5 minutes
            current_time = datetime.now(tz=self.timestamp.tzinfo)
            if (current_time > (self.timestamp + delta)):
                return False
            elif self.expired:
                return False
            else:
                return True
        else:
            return False


    def GenerateOTP():
        generated_code = ''

        for _ in range(6):
            value = str(secrets.choice([0,1,2,3,4,5,6,7,8,9])) 
            generated_code += value
        return generated_code

    def createOTP(self):
         
        while not self.code:
            generatedOTP = OTP.GenerateOTP()
            ref = secrets.token_urlsafe(10)
            object_with_similar_ref = OTP.objects.filter(ref=ref)
            if not object_with_similar_ref:
                self.ref = ref
                self.code = generatedOTP
            send_otp_email(
                subject='OTP VERIFICATION',
                context='Please use the OTP below to confirm your transaction',
                recipient_list=self.user,
                otp=generatedOTP
        )

        super().save()
        return self.code