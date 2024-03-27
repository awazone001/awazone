from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMessage 

def send_email(subject, context, recipient_list,*args,**kwargs):

    email_subject = subject
    email_body = render_to_string('email.html',context)
        
    email = EmailMessage(email_subject, email_body, settings.EMAIL_HOST_USER, [recipient_list],reply_to=None)
    email.content_subtype = "html"
    email.send()

def send_otp_email(subject, context, recipient_list,otp,*args,**kwargs):

    email_subject = subject
    content = {'context': context,'otp': otp}
    email_body = render_to_string('OTP_Email.html',content,*args,**kwargs)
        
    email = EmailMessage(email_subject, email_body, settings.EMAIL_HOST_USER, [recipient_list],reply_to=None)
    email.content_subtype = "html"
    email.send()