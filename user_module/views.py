from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout,authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponse,JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .decorators import user_access_only
from .forms import CreateUserForm, LoginForm, UserUpdateForm, get_dialing_code
from .models import UserProfile, AIBO, Level
from .tokens import account_activation_token
from aibopay.models import AIBOWallet, MonthlyLicense, YearlyLicense, WalletTransaction, BankAccount
from aiboearn.models import AssetPurchases,AssetSales
from messaging_module.models import Notification
from django.db import transaction
from admin_and_staff_module.models import SlidePhoto,TermsAndConditions
from encrypt import hash_password

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
                    referral_code = form.cleaned_data.get('referral_code')
                    
                    if referral_code:
                        referred_by = UserProfile.objects.filter(user_code=referral_code).first()
                        if referred_by:
                            AIBOWallet.create_wallet(user)
                        elif hash_password(referral_code) == settings.ADMIN_REFERENCE:
                            UserProfile.create_admin(user)
                        else:
                            AIBOWallet.create_wallet(user)
                    else:
                        AIBOWallet.create_wallet(user)

                    verify_email_view(request, user)
                    messages.success(request, 'Kindly confirm your email to complete the registration')
                    Notification.create_notification(user=user, message='User Created Successfully')
                    return redirect('user_login')
            except Exception as e:
                print(e)
                messages.error(request, 'An error occurred during registration')
                return render(request, 'signup.html', {'form': form})
        else:
            messages.error(request, 'Invalid input!')
            return render(request, 'signup.html', {'form': form})
    else:
        form = CreateUserForm()
    
    return render(request, 'signup.html', {'form': form})

def sign_in(request):
    if request.method == 'POST':
        try:
            user_form = LoginForm(request.POST)
            if user_form.is_valid():
                user = user_form.clean()
                auth_user = authenticate(username = user['username_or_email'], password= user['password'])
                if auth_user:
                    login(request, auth_user)
                    if auth_user.is_staff:
                        if auth_user.is_superuser:
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
            print(e)
            messages.error(request,'Error Occurred')
    else:
        user_form = LoginForm()
    
    return render(request, 'signin.html', {'form': user_form})

def sign_out(request):
    logout(request)
    return redirect('user_login', permanent=True)

@login_required
def RetrieveUser(request, email):
    if request.user.is_authenticated:
        try:
            user = UserProfile.objects.get(email=email)
            aibo = AIBO.objects.get(user=user)
        except UserProfile.DoesNotExist:
            user = None
        except AIBO.DoesNotExist:
            aibo = None
        
        try:
            wallet = AIBOWallet.objects.get(user=user)
        except AIBOWallet.DoesNotExist:
            wallet = None
        
        monthly_subscriptions = MonthlyLicense.objects.filter(user=user, is_valid=True)
        yearly_subscriptions = YearlyLicense.objects.filter(user=user, is_valid=True)
        referrals = UserProfile.objects.filter(referral_code=user.user_code)
        transactions = WalletTransaction.objects.filter(wallet=wallet)
        account = BankAccount.objects.filter(wallet=wallet)
        assetpurchases = AssetPurchases.objects.filter(user=user)
        assetsales = AssetSales.objects.filter(user=user)
        monthlylicense = MonthlyLicense.get_monthly_license(user = user)
        yearlylicense = YearlyLicense.get_yearly_license(user = user)

        data = {
            "user": user,
            "aibo": aibo,
            "wallet": wallet,
            "MonthlySubscription": monthly_subscriptions,
            "YearlySubscription": yearly_subscriptions,
            "referrals": referrals,
            'transactions': transactions,
            'account': account,
            'assetpurchases': assetpurchases,
            'assetsales': assetsales,
            'monthlylicense' : monthlylicense,  
            'yearlylicense' : yearlylicense
        }
        return data
    return None

@login_required
@user_access_only()
def user_dashboard(request):
    content = {
        'data' : RetrieveUser(request=request, email=request.user.email),
        'slides': SlidePhoto.objects.all()
    }
    return render(request, 'user_view_dashboard.html', content)

@login_required
@user_access_only()
def view_profile(request):
    content = {
        'data' : RetrieveUser(request=request, email=request.user.email),
    }
    return render(request, 'user_view_profile.html', content)

@login_required
@user_access_only()
def update_profile(request):
    user = UserProfile.objects.get(email=request.user.email)
    try:
        if request.method == 'POST':
            update_form = UserUpdateForm(request.POST, request.FILES)  # Pass dialing code to form
            if update_form.is_valid():
                user.profile_image = update_form.cleaned_data['profile_image']
                user.phone_number = update_form.cleaned_data['phone_number']
                user.save() 
                messages.info(request, 'User Details Updated!')
                return redirect('user_profile')
        else:
            update_form = UserUpdateForm(instance=user)  # Pass dialing code to form
    except Exception as e:
        messages.error(request, f'Error Occurred: {e}')
    content = {
        'data': RetrieveUser(request=request, email=request.user.email),
        'update_form': update_form,    
        }
    return render(request, 'user_update_profile.html', content)



@login_required
@user_access_only()
def view_rank(request):
    ranks = Level.objects.all()
    if ranks.count() == 0:
        ranks = None

    content = {
        'data': RetrieveUser(request=request, email=request.user.email),
        'ranks': ranks,
    }
    return render(request, 'user_view_ranks.html', content)

@login_required
@user_access_only()
def view_direct_referrals(request):
    content = {
        'data' : RetrieveUser(request=request, email=request.user.email),
    }
    return render(request, 'user_view_referrals.html', content)