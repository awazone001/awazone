from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponse,JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .decorators import user_access_only
from .forms import CreateUserForm, LoginForm, TestimonialForm, UserUpdateForm
from .models import UserProfile, AIBO, Reward, Level
from .tokens import account_activation_token
from aibopay.models import AIBOWallet, MonthlyLicense, YearlyLicense
from messaging_module.models import Notification
from django.db import transaction
from admin_and_staff_module.models import SlidePhoto,TermsAndConditions

def view_terms_and_conditions(request):
    if request.method == 'GET':
        try:
            terms_and_conditions = TermsAndConditions.objects.latest('last_updated')
            content = {
                'title': terms_and_conditions.title,
                'content': terms_and_conditions.content
            }
            return JsonResponse(content)
        except TermsAndConditions.DoesNotExist:
            return JsonResponse({'error': 'Terms and conditions not found'}, status=404)
    else:
        # Handle other HTTP methods if needed
        return JsonResponse({'error': 'Method not allowed'}, status=405)

def verify_email_view(request, user):
    current_site = get_current_site(request)
    mail_subject = 'Activation link has been sent to your email id'
    message = render_to_string('activation_email.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    })
    to_email = user.email
    email = EmailMessage(
        mail_subject, message, to=[to_email]
    )
    email.content_subtype = "html"
    email.send()
    return HttpResponse('Please confirm your email address to complete the registration')

def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = UserProfile.objects.get(id=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Thank you for your email confirmation. Now you can login your account.')
        return render(request, 'activation_success.html')
    else:
        if request.method == 'POST':
            verify_email_view(request, user)
            messages.success(request, 'Kindly Check your mail for new link to veify Account')
            return redirect('user_login', permanent=True)
        else:
            return render(request, 'activation_failed.html')

def sign_up(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=True)
                    referral_code = form.cleaned_data['referral_code']
                    if referral_code == settings.ADMIN_REFERENCE:
                        UserProfile.create_admin(user)
                    else:
                        UserProfile.create_user(user)
                        AIBOWallet.create_wallet(user)

                    verify_email_view(request, user)
                    messages.success(request, 'Kindly confirm your email to complete the registration')
                    Notification.create_notification(user=user, message='User Created Successfully')
                    return redirect('user_login', permanent=True)
            except Exception as e:
                print(e)
                messages.error(request, f"Error Occurred")
                return render(request, 'signup.html', {'form': form})
        else:
            messages.error(request, "Invalid Input!")
            return render(request, 'signup.html', {'form': form})
    else:
        form = CreateUserForm()
    
    return render(request, 'signup.html', {'form': form})

def sign_in(request):
    if request.method == 'POST':
        try:
            form = LoginForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']
                user = authenticate(request, username=email, password=password)
                if user is not None:
                    if not user.is_active:
                        messages.error(request, 'Kindly confirm your email to complete the registration Or contact support')
                    else:
                        login(request, user)
                        if user.is_staff:
                            if user.is_superuser:
                                return redirect('admin_dashboard', permanent=True)
                            else:
                                return redirect('staff_dashboard', permanent=True)
                        else:
                            return redirect('user_dashboard', permanent=True)
                else:
                    messages.error(request, 'Email or Password Incorrect!')
            else:
                messages.error(request, 'Invalid Input!')
        except Exception as e:
            messages.error(request,'Error Occurred')
    else:
        form = LoginForm()
    
    return render(request, 'signin.html', {'form': form})

def sign_out(request):
    logout(request)
    return redirect('user_login', permanent=True)

@login_required
@user_access_only()
def user_dashboard(request):
    user = UserProfile.objects.get(email=request.user)
    monthly_subscriptions = MonthlyLicense.objects.filter(user=user, is_valid=True)
    yearly_subscriptions = YearlyLicense.objects.filter(user=user, is_valid=True)
    content = {
        'user': user,
        'aibo': AIBO.objects.get(user=user),
        'wallet': AIBOWallet.objects.get(user=user),
        'monthly': monthly_subscriptions,
        'yearly': yearly_subscriptions,
        'slides': SlidePhoto.objects.all()
    }
    return render(request, 'user_view_dashboard.html', content)

@login_required
@user_access_only()
def view_profile(request):
    user = UserProfile.objects.get(id=request.user.id)
    content = {
        'user': user,
        'user_wallet': AIBOWallet.objects.get(user=user),
        'aibo': AIBO.objects.get(user=user),
        'referrals': UserProfile.objects.filter(referral_code=user.user_code),
    }
    return render(request, 'user_view_profile.html', content)

@login_required
@user_access_only()
def update_profile(request):
    user = UserProfile.objects.get(email=request.user.email)
    try:
        if request.method == 'POST':
            update_form = UserUpdateForm(request.POST, request.FILES)
            if update_form.is_valid():
                user.profile_image = update_form.cleaned_data['profile_image']
                user.phone_number = update_form.cleaned_data['phone_number']
                user.save() 
                messages.info(request, 'User Details Updated!')
                return redirect('user_profile')
            else:
                user.profile_image = update_form.cleaned_data['profile_image']
                user.phone_number = update_form.cleaned_data['phone_number']
                user.save()
                messages.info(request, 'User Details Updated!')
                return redirect('user_profile')
        else:
            update_form = UserUpdateForm(instance=user)
    except Exception as e:
        messages.error(request, f'Error Occurred: {e}')
    content = {
        'user': user,
        'user_wallet': AIBOWallet.objects.get(user=user),
        'aibo': AIBO.objects.get(user=user),
        'update_form': update_form,
    }
    return render(request, 'user_update_profile.html', content)

@login_required
@user_access_only()
def view_level(request):
    searched_user = UserProfile.objects.get(email=request.user.email)
    user_wallet = AIBOWallet.objects.get(user=searched_user.id)
    user_info = AIBO.objects.get(user=searched_user.id)
    levels = Level.objects.all()
    content = {
        'user': searched_user,
        'user_wallet': user_wallet,
        'aibo': user_info,
        'levels': levels,
    }
    return render(request, 'user_view_levels.html', content)

@login_required
@user_access_only()
def verify_level(request):
    searched_user = UserProfile.objects.get(email=request.user.email)
    user_level = Level.objects.get(title = AIBO.objects.get(user=searched_user).level)
    user_reward = Reward.objects.get(user=searched_user, user_level=user_level.level)
    
    if request.method == 'POST':
        testimonial = TestimonialForm(request.POST)
        if testimonial.is_valid():
            user_reward.title = testimonial.cleaned_data['title']
            user_reward.testimonial = testimonial.cleaned_data['testimonial']
            user_reward.recieved = testimonial.cleaned_data['recieved']
            user_reward.save()
            messages.success(request, 'You have completed verification!')
            return redirect('user_dashboard')
        else:
            messages.error(request, 'Invalid Input')
            testimonial = TestimonialForm(request.POST)
    else:
        testimonial = TestimonialForm(request.POST)
    
    content = {
        'user': searched_user,
        'user_wallet': AIBOWallet.objects.get(user=searched_user.id),
        'aibo': AIBO.objects.get(user=searched_user.id),
        'level': user_level,
        'reward': user_reward,
        'testimonial': testimonial,
    }
    return render(request, 'user_verify_level.html', content)