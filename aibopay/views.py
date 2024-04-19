from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseBadRequest
from django.db.models import Q
from paystackapi.paystack import Paystack
import base64
import json
import hashlib
from user_module.models import UserProfile,AIBO
from user_module.decorators import user_access_only
from messaging_module.models import Notification, OTP
from messaging_module.forms import OTPForm
from .models import WalletTransaction,AIBOWallet,AIBORates,BankAccount
from .paystack_verification import (
    get_supported_banks,get_bank_name,get_user_accounts
    )
from .forms import (
    ResetPINForm, VerifyAccountForm, PINVerificationForm,WithdrawalForm,AIBORatesForm,DepositForm
    )
from user_module.decorators import user_access_only,staff_access_only,admin_access_only
from django.conf import settings
from django.db import transaction as  db_transaction
from user_module.views import RetrieveUser

@login_required
@user_access_only()
def aibopay_dashboard(request):
    content = {
        'data' : RetrieveUser(request=request, email=request.user.email),
    }
    return render(request, 'aibopay.html', content)

@login_required
@user_access_only()
def deposit(request):
    searched_user = UserProfile.objects.get(email = request.user)
    deposit_form = DepositForm(request.POST)
    if request.method == 'POST':
        if  deposit_form.is_valid():
            with db_transaction.atomic():
                amount = deposit_form.cleaned_data['amount']
                description = deposit_form.cleaned_data['description']

                paystack_secret_key = settings.PAYSTACK_SECRET_KEY
                paystack = Paystack(secret_key=paystack_secret_key)

                payment = WalletTransaction.objects.create(
                    wallet = AIBOWallet.objects.get(user=request.user),
                    transaction_type='Deposit',
                    email=request.user.email,
                    amount=amount,
                    description = description
                )
                payment.save()

                transaction = paystack.transaction.initialize(
                    amount=payment.amount_value(),
                    email=searched_user.email,
                    callback_url=request.build_absolute_uri('authenticate_deposit'),
                    transaction_charge=0,
                    currency='NGN',
                    timeout=18000,
                )

                payment.ref = transaction['data']['reference']
                payment.save()

                return redirect(transaction['data']['authorization_url'])
        else:
            messages.error(request, "Invalid Amount")

    return render(request, 'aibopay_deposit.html', {
        'deposit': deposit_form,
        'data' : RetrieveUser(request=request, email=request.user.email),
    })

@login_required
@user_access_only()
def authenticate_deposit(request):
    if request.method == 'GET':
        transaction_reference = request.GET.get('reference')

        paystack_secret_key = settings.PAYSTACK_SECRET_KEY
        paystack = Paystack(secret_key=paystack_secret_key)

        verification = paystack.transaction.verify(transaction_reference)

        if verification['data']['status'] == 'success':
            payment = WalletTransaction.objects.get(ref=transaction_reference)
            if payment.status == 'Pending':
                user_wallet = AIBOWallet.objects.get(user=request.user)
                user_wallet.balance += payment.amount
                user_wallet.save()
                payment.status = 'Success'
                payment.save()
                Notification.create_notification(user = UserProfile.objects.get(email=request.user),
                                                 message=f'Your deposit of NGN {payment.amount} was Successful')
                return render(request, 'aibopay_deposit_success.html', {'amount': payment.amount, 'wallet': payment})
            else:
                return redirect('user_dashboard', permanent=True)

    payment = WalletTransaction.objects.get(ref=transaction_reference)
    return render(request, 'aibopay_deposit_failed.html', {'amount': payment.amount, 'wallet': payment.wallet})

@login_required
@admin_access_only()
def manage_rates(request):
    if request.method == 'POST':
        RatesForm = AIBORatesForm(request.POST)
        if RatesForm.is_valid():
            RatesForm.save(commit=True)
            messages.success(request, 'Rates Updated Successfully!')
        else:
            messages.error(request, 'Rates Update Failed!')
    try:
        latest_rates_instance = AIBORates.objects.latest('created_at')
        RatesForm = AIBORatesForm(instance=latest_rates_instance)
    except AIBORates.DoesNotExist:
        RatesForm = AIBORatesForm()


    content = {'form': RatesForm}
    return render(request, 'admin_update_rate.html', content)

@login_required
@user_access_only()
def resetpin(request):
    searched_user = UserProfile.objects.get(email=request.user)
    user_wallet = AIBOWallet.objects.get(user=searched_user)
    try:
        if request.method == 'POST':
            PINForm = ResetPINForm(request.POST)
            if PINForm.is_valid():
                new_pin = PINForm.cleaned_data['pin']
                confirm_pin = PINForm.cleaned_data['confirm_pin']
                if new_pin == confirm_pin:
                    pin_bytes = bytes(new_pin, 'utf-8')
                    encoded_pin = base64.b64encode(pin_bytes).decode('utf-8')
                    data = {'pin': encoded_pin}
                    request.session['data'] = data
                    createOTP = OTP(user=searched_user)
                    createOTP.createOTP()  # Create an OTP for the newly set up PIN
                    messages.success(request, 'Check Your Email for OTP')
                    return redirect('reset_pin_confirmation', createOTP.ref, permanent=True)
                else:
                    messages.error(request, 'PINs do not match!')
            else:
                PINForm = ResetPINForm(request.POST)
        else:
            PINForm = ResetPINForm(request.POST)
    except Exception as e:
        print(e)
        messages.error(request, 'Error Occurred!')

    content = {
        'data' : RetrieveUser(request=request, email=request.user.email),
        'pin': PINForm,
    }
    return render(request, 'reset_pin.html', content)

@login_required
@user_access_only()
def resetpin_otp_confirmation(request, id):
    searched_user = UserProfile.objects.get(email=request.user)
    user_wallet = AIBOWallet.objects.get(user=searched_user)

    if request.method == 'POST':
        try:
            OTPForm_ = OTPForm(request.POST)
            if OTPForm_.is_valid():
                recent_otp = OTP.objects.get(
                    Q(user=searched_user),
                    Q(expired=False),
                    Q(ref=id)
                )
                code = OTPForm_.cleaned_data['code']
                pin = request.session.get('data')
                if recent_otp.isValidCode(code) == True:
                    user_wallet.pin = pin['pin']
                    user_wallet.save()
                    recent_otp.expired = True
                    recent_otp.save()
                    del request.session['data']
                    messages.success(request, 'Your PIN Reset was Successful!')
                    return redirect('user_dashboard', permanent=True)
                else:
                    user_wallet.pin = None
                    user_wallet.save()
                    messages.error(request, 'OTP Expired or Incorrect OTP')
            else:
                OTPForm_ = OTPForm(request.POST)
        except Exception as e:
            messages.error(request, 'OTP Expired or Incorrect OTP')
    else:
        OTPForm_ = OTPForm(request.POST)
    content = {
        'data' : RetrieveUser(request=request, email=request.user.email),
        'otp': OTPForm_,
    }
    return render(request, 'OTP_Form.html', content)

@login_required
@user_access_only()
def resend_otp(request):
    searched_user = UserProfile.objects.get(email=request.user)
    createOTP = OTP(user =  searched_user)
    createOTP.createOTP() # Create an OTP for the newly set up PIN

    messages.success(request, 'Check your email for OTP')
    return redirect('reset_pin_confirmation', createOTP.ref, permanent=True)

@login_required
@user_access_only()
def payout_account(request):
    content = {
        'data' : RetrieveUser(request=request, email=request.user.email),
    }
    return render(request, 'aibopay_accounts.html', content)

@login_required
@user_access_only()
def add_account(request):
    searched_user = UserProfile.objects.get(email=request.user)
    user_wallet = AIBOWallet.objects.get(user=searched_user)
    user_info = AIBO.objects.get(user=searched_user)
    bank_list = get_supported_banks()

    if request.method == 'POST':
        VerificationForm = VerifyAccountForm(request.POST)
        if VerificationForm.is_valid():
            account_number = VerificationForm.cleaned_data['account_number']
            bank_code = request.POST.get('bank')
            bank_name = get_bank_name(bank_code)

            try:
                paystack_secret_key = settings.PAYSTACK_SECRET_KEY
                paystack = Paystack(secret_key=paystack_secret_key)

                response = paystack.verification.verify_account(
                    account_number=account_number,
                    bank_code=bank_code
                )
                if response['status'] == True:
                    data = {
                        'bank_name' : bank_name,
                        'bank_id' : response['data']['bank_id'],
                        'bank_code': bank_code,
                        'account_number' : account_number.upper(),
                        'account_name' : response['data']['account_name'],
                    }
                    request.session['data'] = data
                    messages.success(request, 'Confirm the account details and Input your wallet PIN to confirm the Account')
                    return redirect('confirm_account', account_number, permanent=True)
                else:
                    error_message = response['message']
                    messages.error(request, f'{error_message}')
                    return redirect('verify_account', permanent=True)
            except Exception as e:
                messages.error(request, f'An Error Occurred Confirm Details Again')
                return redirect('verify_account', permanent=True)
        else:
            messages.error(request, 'Invalid Input')
    else:
        VerificationForm = VerifyAccountForm(request.POST)
    content = {
        'data' : RetrieveUser(request=request, email=request.user.email),
        'verify': VerificationForm,
        'banks': bank_list,
    }
    return render(request, 'aibopay_add_account.html', content)

@login_required
@user_access_only()
def verify_account(request, id):
    searched_user = UserProfile.objects.get(email=request.user)
    user_wallet = AIBOWallet.objects.get(user=searched_user)
    user_info = AIBO.objects.get(user=searched_user)
    data = request.session.get('data')

    if request.method == 'POST':
        PINForm = PINVerificationForm(request.POST)
        if PINForm.is_valid():
            pin_bytes = bytes(PINForm.cleaned_data['pin'], 'utf-8')
            encoded_pin = base64.b64encode(pin_bytes).decode('utf-8')
            if encoded_pin == user_wallet.pin:
                BankAccount.create_account(data,user_wallet)
                del request.session['data']
                messages.success(request, f'{data['bank_name']} account with account number {data['account_number']} Added Successfully')
                return redirect('payout_account', permanent=True)
            elif str(user_wallet.pin) is None:
                messages.error(request, 'Set Your Wallet PIN')
                return redirect('reset_pin', permanent=True)
            else:
                messages.error(request, 'Incorrect PIN')
        else:
            messages.error(request, 'Invalid Input')
    else:
        PINForm = PINVerificationForm(request.POST)

    content = {
        'data' : RetrieveUser(request=request, email=request.user.email),
        'form': PINForm,
        'account': data,
    }
    return render(request, 'aibopay_confirm_account.html', content)

@login_required
@user_access_only()
def delete_account(request, id):
    account = BankAccount.objects.get(
        Q(wallet = AIBOWallet.objects.get(user = request.user)) &
        Q(id=id)
    )
    account.delete()
    messages.success(request, f'{account.account_number} deleted successfully')
    return redirect('payout_account', permanent=True)

@login_required
@user_access_only()
def withdraw(request):
    try:
        searched_user = UserProfile.objects.get(email=request.user)
        user_wallet = AIBOWallet.objects.get(user=searched_user)
        user_info = AIBO.objects.get(user=searched_user)
        banks = get_user_accounts(user_wallet)

        if request.method == 'POST':
            WithdrawForm = WithdrawalForm(request.POST)
            if WithdrawForm.is_valid():
                amount = WithdrawForm.cleaned_data['amount']
                description = WithdrawForm.cleaned_data['description']
                bank = request.POST.get('bank')
                chosen_bank = BankAccount.objects.get(id=bank)
                if amount <= user_wallet.balance:
                    try:
                        paystack_secret_key = settings.PAYSTACK_SECRET_KEY
                        paystack = Paystack(secret_key=paystack_secret_key)

                        withdrawal = WalletTransaction.objects.create(
                            wallet = user_wallet,
                            transaction_type='Withdraw',
                            email=request.user.email,
                            description=description,
                            amount = amount,
                            recipient = chosen_bank,
                            status = 'Pending'
                        )

                        withdrawal.save()

                        withdrawal_response_ = paystack.transferRecipient.create(
                            type="nuban",
                            name=chosen_bank.account_name,
                            account_number=chosen_bank.account_number,
                            bank_code=chosen_bank.bank_code,
                            email=searched_user.email,
                            phone_number=''
                        )

                        recipient_code = withdrawal_response_['data']['recipient_code']

                        withdrawal_response = paystack.transfer.initiate(
                            source="balance",
                            reason=description,
                            amount=withdrawal.amount_value(),
                            recipient=recipient_code
                        )
                        withdrawal.ref = withdrawal_response['data']['reference']
                        withdrawal.save()

                        if withdrawal_response["status"] == True:
                            return redirect('pin_confirmation', withdrawal.ref, permanent=True)
                        elif withdrawal_response["status"] == False:
                            withdrawal.status = 'Failed'
                            return render(request, 'aibopay_withdrawal_failed.html',
                                          {'amount': withdrawal.amount, 'wallet': user_wallet, 'bank': chosen_bank})
                        else:
                            WithdrawForm = WithdrawalForm(request.POST)
                            messages.error(request, 'An Error Occurred')
                    except Exception as e:
                        print(e)
                        WithdrawForm = WithdrawalForm(request.POST)
                        messages.error(request, f'Error Occurred')
                else:
                    WithdrawForm = WithdrawalForm(request.POST)
                    messages.error(request, 'Insufficient Balance')
            else:
                WithdrawForm = WithdrawalForm(request.POST)
                messages.error(request, 'Invalid data')
        else:
            WithdrawForm = WithdrawalForm(request.POST)

        content = {
            'data' : RetrieveUser(request=request, email=request.user.email),
            'withdrawal': WithdrawForm,
            'banks': banks,
        }

        return render(request, 'aibopay_withdraw.html', content)
    except ObjectDoesNotExist:
        return render(request, 'Error_403.html')

@login_required
@user_access_only()
def authenticate_PIN(request, ref):
    searched_user = UserProfile.objects.get(email=request.user)
    user_wallet = AIBOWallet.objects.get(user=searched_user)
    user_info = AIBO.objects.get(user=searched_user)
    if request.method == 'POST':
        try:
            PINForm = PINVerificationForm(request.POST)
            if PINForm.is_valid():
                pin_bytes = bytes(PINForm.cleaned_data['pin'], 'utf-8')
                encoded_pin = base64.b64encode(pin_bytes).decode('utf-8')
                if encoded_pin == user_wallet.pin:
                    payment = WalletTransaction.objects.get(ref=ref)
                    return render(request, 'aibopay_withdrawal_success.html', {
                        'amount': payment.amount,
                        'wallet': user_wallet,
                        'bank': payment.recipient
                    })
                else:
                    messages.error(request, 'Incorrect PIN')
            else:
                messages.error(request, 'Invalid PIN format')
        except Exception as e:
            print(e)
            messages.error(request,'Error Occurred')
    else:
        PINForm = PINVerificationForm(request.POST)

    content = {
        'data' : RetrieveUser(request=request, email=request.user.email),
        'pin': PINForm
    }
    return render(request, 'PINForm.html', content)

@login_required
@staff_access_only()
def complete_withdrawal(request, ref):
    if request.method == 'POST':
        payload = json.loads(request.body)
        secret_key = settings.PAYSTACK_SECRET_KEY
        computed_signature = hashlib.sha512((secret_key + payload['event'] + payload['data']['reference']).encode()).hexdigest()
        webhook_signature = request.headers.get('X-Paystack-Signature')
        
        if computed_signature != webhook_signature:
            return HttpResponseBadRequest("Invalid webhook signature")

        event = payload['event']
        if event == 'transfer.success':
            reference = payload['data']['reference']

            try:
                payment = WalletTransaction.objects.get(ref=reference)
                payment.verified = True
                payment.save()

                user_wallet = AIBOWallet.objects.get(wallet_number=payment.wallet)
                user_wallet.balance -= payment.amount
                user_wallet.outflow -= payment.amount
                user_wallet.save()

                recipient_account = AIBOWallet.objects.get(id=payment.recipient)
                recipient_account.payout += payment.amount
                recipient_account.save()

                Notification.create_notification(user=request.user.profile, message=f'Your Withdrawal of {payment.currency} {payment.amount} was Successful')

                return HttpResponse(status=200)
                
            except WalletTransaction.DoesNotExist:
                return HttpResponseBadRequest("Payment not found")
        
    return render(request, 'otp_form.html')