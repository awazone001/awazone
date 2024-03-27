from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render,redirect
from django.http import JsonResponse
from django.db import transaction
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponseServerError
from .models import Sector,Asset,AssetPurchases,AssetSales
from .forms import AssetSales,AssetPurchaseForm,AssetForm,SectorForm,AssetSaleForm
from user_module.decorators import user_access_only,staff_access_only,admin_access_only
from user_module.models import UserProfile
from aibopay.models import AIBOWallet,WalletTransaction,AIBORates,MonthlyLicense,YearlyLicense
from messaging_module.models import Notification
from user_module.models import AIBO
from datetime import timedelta
from decimal import Decimal

@login_required
@user_access_only()
def aiboearn_dashboard(request):
    return _render_aiboearn_page(request, 'user_view_aiboearn.html')

@login_required
@user_access_only()
def aiboearn_asset_sales(request, purchase_id):
    content = {
        'purchases': AssetPurchases.objects.get(id=purchase_id),
        'sales': AssetSales.objects.filter(purchase=purchase_id),
    }
    return _render_aiboearn_page(request, 'user_view_aiboearn_sales.html', content)

@login_required
@user_access_only()
def user_view_sector(request):
    return _render_aiboearn_page(request, 'user_view_aiboearn_sector.html')

@login_required
@user_access_only()
def user_view_asset(request):
    return _render_aiboearn_page(request, 'user_view_aiboearn_assets.html')

@login_required
@user_access_only()
def user_view_sector_asset(request, aibo_sector):
    assets = Asset.objects.filter(sector = Sector.objects.get(sector=aibo_sector).id)
    content = {'assets': assets}
    return _render_aiboearn_page(request, 'user_view_aiboearn_assets.html', content)

def _render_aiboearn_page(request, template_name, extra_context=None):
    searched_user = UserProfile.objects.get(email=request.user)
    context = {
        'user': searched_user,
        'user_wallet': AIBOWallet.objects.get(user=searched_user),
        'aibo': AIBO.objects.get(user=searched_user),
        'purchases': AssetPurchases.objects.filter(user=request.user),
        'sales': AssetSales.objects.filter(user=request.user),
        'assets': Asset.objects.all(),
        'sectors': Sector.objects.all(),
    }
    if extra_context:
        context.update(extra_context)
    return render(request, template_name, context)

@login_required
@admin_access_only()
def add_asset(request):
    if request.method == 'POST':
        new_asset = AssetForm(request.POST, request.FILES)
        if new_asset.is_valid():
            with transaction.atomic(durable=True, savepoint=True):
                new_asset.save(commit=True)
                messages.success(request, 'Asset Successfully Added!')
                return redirect('view_assets')
        else:
            messages.error(request, 'Invalid Inputs')
    else:
        new_asset = AssetForm()
    
    content = {
        'staff': UserProfile.objects.get(email=request.user),
        'new_asset': new_asset
    }
    return render(request, 'admin_add_new_asset.html', content)

@login_required
@admin_access_only()
def update_asset(request, asset_id):
    asset_instance = get_object_or_404(Asset, id=asset_id)
    if request.method == 'POST':
        updated_asset = AssetForm(request.POST, request.FILES, instance=asset_instance)
        if updated_asset.is_valid():
            with transaction.atomic(durable=True, savepoint=True):
                updated_asset = updated_asset.save(commit=True)
                messages.success(request, f'{asset_instance.asset} Successfully Updated!')
                return redirect('view_assets')
        else:
            messages.error(request, 'Invalid Inputs')
    else:
        updated_asset = AssetForm(instance=asset_instance)

    content = {
        'staff': UserProfile.objects.get(email=request.user),
        'new_asset': updated_asset,
        'sector': get_object_or_404(Asset, id=asset_id).sector
    }
    return render(request, 'admin_add_new_asset.html', content)

@login_required
@staff_access_only()
def view_asset(request):
    purchase = AssetPurchases.objects.all().order_by('-transaction_datetime')
    sale = AssetSales.objects.all().order_by('-transaction_datetime')
    assets = Asset.objects.all().order_by('sector')
    sectors = Sector.objects.all()

    content = {
        'staff': UserProfile.objects.get(email=request.user),
        'purchases': purchase,
        'sales': sale,
        'assets': assets,
        'sectors': sectors,
    }
    return render(request, 'admin_view_asset.html', content)

@login_required
@admin_access_only()
def add_sector(request):
    new_sector = SectorForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if new_sector.is_valid():
            create_sector = new_sector.save(commit=False)
            create_sector.sector = create_sector.sector.upper()
            create_sector.save()
            messages.success(request, 'Sector Successfully Added!')
            return redirect('view_sectors')
        else:
            messages.error(request, 'Invalid Inputs')

    content = {
        'staff': UserProfile.objects.get(email=request.user),
        'new_sector': new_sector
    }
    return render(request, 'admin_add_new_sector.html', content)

@login_required
@admin_access_only()
def update_sector(request, sector_id):
    sector_instance = get_object_or_404(Sector, id=sector_id)
    new_sector = SectorForm(request.POST or None, request.FILES or None, instance=sector_instance)
    if request.method == 'POST':
        if new_sector.is_valid():
            with transaction.atomic(durable=True, savepoint=True):
                updated_sector = new_sector.save(commit=False)
                updated_sector.sector = updated_sector.sector.upper()
                updated_sector.save()
                messages.success(request, f'{sector_instance.sector} Successfully Updated!')
                return redirect('view_sectors')
        else:
            messages.error(request, 'Invalid Inputs')

    content = {
        'staff': UserProfile.objects.get(email=request.user),
        'new_sector': new_sector,
        'sector': sector_instance
    }
    return render(request, 'admin_add_new_sector.html', content)

@login_required
@user_access_only()
def aiboearn_asset_purchase(request):
    if request.method == 'POST':
        return _process_asset_purchase(request)
    else:
        purchase_form = AssetPurchaseForm()
        return _render_asset_purchase_page(request, purchase_form)

def _process_asset_purchase(request):
    searched_user = UserProfile.objects.get(email=request.user)
    user_wallet = AIBOWallet.objects.get(user=searched_user)
    purchase_form = AssetPurchaseForm(request.POST)
    
    try:
        if purchase_form.is_valid():
            if user_wallet.balance >=  purchase_form.cleaned_data["amount"]:
                asset = purchase_form.cleaned_data['asset']
                sector = purchase_form.cleaned_data['sector']
                amount = purchase_form.cleaned_data['amount']
                # Process purchase
                purchase_status = _purchase_asset(request, asset, sector, amount,user_wallet)
                if purchase_status == True:
                    content = {
                        'user': searched_user,
                        'user_wallet': user_wallet,
                        'aibo': UserProfile.objects.get(email = searched_user),
                        'asset' : asset,
                        'amount': amount
                    }
                    return render(request,'aiboearn_purchase_asset_success.html',content)
                return messages.error(request,f"Asset Purchase Failed: {purchase_status}")
            messages.error(request,'Insufficient Balance!')
        else:
            messages.error(request, 'Invalid input')  
    except Exception as e:
        print(e)
        messages.error(request, 'Error processing your request')

    return _render_asset_purchase_page(request, purchase_form)

def _purchase_asset(request, asset, sector, amount, user_wallet):
    purchased_sector = Sector.objects.get(sector=sector)
    purchased_asset = Asset.objects.get(asset=asset)

    try:
        if purchased_sector.is_available:
            if purchased_asset.is_available:
                sold_out_volume = Decimal(purchased_asset.sold_out_volume)
                share_rate = Decimal(purchased_asset.share_rate)
                total_shares = Decimal(purchased_asset.total_shares)
                minimum_purchase_amount = Decimal(purchased_asset.minimum_purchase_amount)

                if sold_out_volume + Decimal(amount) / share_rate <= total_shares:
                    if Decimal(amount) >= minimum_purchase_amount:
                        new_transaction = WalletTransaction.objects.create(
                            wallet=user_wallet,
                            transaction_type='Purchase',
                            email=request.user.email,
                            description='AIBOEARN ASSET PURCHASE',
                            amount=Decimal(amount),
                            status='Success'
                        )
                        new_transaction.save()

                        share_value = Decimal(amount) / share_rate

                        new_purchase = AssetPurchases.objects.create(
                            id=new_transaction.ref,
                            user=request.user,
                            amount=Decimal(amount),
                            sector=purchased_sector,
                            asset=purchased_asset,
                            share_value=share_value
                        )

                        new_purchase.expiring_datetime = new_purchase.transaction_datetime + timedelta(
                            days=purchased_asset.maximum_duration)
                        new_purchase.save()

                        # Increases the total share bought after deposit is made
                        previous_shares = Decimal(purchased_asset.sold_out_volume)
                        purchased_asset.sold_out_volume = previous_shares + (Decimal(amount) / share_rate)
                        purchased_asset.percentage_bought = ((previous_shares + (Decimal(amount) / share_rate)) * 100) / total_shares
                        purchased_asset.save()

                        # Debit user's account
                        currency_balance = user_wallet.balance
                        user_wallet.balance = currency_balance - Decimal(amount)
                        user_wallet.save()

                        email_subject = 'AIBO EARN ASSET PURCHASE'
                        email_body = render_to_string('aiboearn_asset_purchase_mail.html', {
                            'recipient_name': request.user.email,
                            'asset': new_purchase,
                            'bought_asset': purchased_asset,
                            'user': request.user
                        })

                        email = EmailMessage(email_subject, email_body, settings.EMAIL_HOST_USER,
                                             [request.user.email], reply_to=None)
                        email.content_subtype = "html"
                        email.send()
                        Notification.create_notification(user=request.user,
                                                         message=f'Your purchase of {asset} worth NGN {new_purchase.amount} was Successful')
                        return True
                    else:
                        return f'Attempted purchase amount is below the minimum purchase for {purchased_asset}'
                else:
                    return f'Attempted Purchase exceeds available Shares for {asset}'
            else:
                return f'{asset} is not available for purchase!'
        else:
            return f'Assets from {sector} are not available for purchase'
    except Exception as e:
        print(e)
        return messages.error(request, f'An Error Occured')

def _render_asset_purchase_page(request, purchase_form):
    searched_user = UserProfile.objects.get(email=request.user)
    user_wallet = AIBOWallet.objects.get(user=searched_user)

    content = {
        'user': searched_user,
        'user_wallet': user_wallet,
        'aibo': AIBO.objects.get(user=searched_user),
        'purchases': AssetPurchases.objects.filter(user=request.user),
        'sales': AssetSales.objects.filter(user=request.user),
        'purchase': purchase_form,
    }

    return render(request, 'aiboearn_purchase_asset.html', content)

@login_required
@user_access_only()    
def ajax_load_assets(request):
    main_value = request.GET.get('main_value')

    # Assuming `main_value` corresponds to the value of the selected sector
    # Retrieve assets based on the selected sector value
    assets = Asset.objects.filter(sector=main_value).order_by('asset')

    # Create a dictionary containing the assets data
    assets_data = [{'pk': asset.pk, 'fields': {'asset': asset.asset}} for asset in assets]

    # Return the assets data as JSON response
    return JsonResponse({'assets': assets_data})

@login_required
@user_access_only()
def aiboearn_sell_asset(request, purchase_id):
    searched_user = get_object_or_404(UserProfile, email=request.user)
    user_wallet = get_object_or_404(AIBOWallet, user=searched_user)
    aibo = get_object_or_404(AIBO, user=searched_user)
    purchase = get_object_or_404(AssetPurchases, user=searched_user, id=purchase_id)
    bought_asset = get_object_or_404(Asset, asset=purchase.asset)

    if request.method == 'POST':
        form = AssetSaleForm(request.POST)
        if form.is_valid():
            amount = Decimal(form.cleaned_data['amount'])
            try:
                with transaction.atomic(durable=True, savepoint=True):
                    expected_value = (Decimal(bought_asset.rate) / Decimal(100.0)) * Decimal(purchase.amount) * Decimal(bought_asset.maximum_duration)
                    share_worth = (amount * Decimal(purchase.share_value)) / expected_value

                    if searched_user.is_active:
                        if amount <= purchase.available_balance:
                            new_transaction = WalletTransaction.objects.create(
                                wallet=user_wallet,
                                transaction_type='Transfer',
                                email=searched_user.email,
                                description='AIBO ASSET SALES',
                                currency = user_wallet.currency,
                                amount = amount,
                                status = 'Success'
                            )
                            new_transaction.save()

                            new_sale = AssetSales.objects.create(
                                id=new_transaction.ref,
                                user=searched_user,
                                purchase=purchase,
                                amount=amount,
                                share_value=round(share_worth, 2)
                            )
                            new_sale.save()

                            user_wallet.balance += amount
                            user_wallet.save()

                            purchase.available_balance -= amount
                            purchase.ledger_balance -= amount
                            purchase.total_sale += amount
                            purchase.save()

                            bought_asset.sold_out_volume -= share_worth
                            bought_asset.percentage_bought = ((bought_asset.sold_out_volume) / bought_asset.total_shares) * Decimal(100)
                            bought_asset.save()

                            email_subject = 'AIBO EARN ASSET PURCHASE'
                            email_body = render_to_string('aiboearn_asset_sales_mail.html', {
                                'recipient_name': searched_user.email,
                                'asset': purchase,
                                'sale': new_sale,
                                'bought_asset': bought_asset,
                                'user': searched_user
                            })

                            email = EmailMessage(email_subject, email_body, settings.EMAIL_HOST_USER,
                                                [searched_user.email], reply_to=None)
                            email.content_subtype = "html"
                            email.send()

                            success_content = {
                                'user': searched_user,
                                'user_wallet': user_wallet,
                                'aibo': aibo,
                                'asset': purchase,
                                'sale': new_sale,
                                'bought_asset': bought_asset,
                            }
                            Notification.create_notification(user=searched_user,
                                                             message=f'Your sale of {bought_asset.asset} shares worth {new_sale.currency}{new_sale.amount} was Successful')
                            return render(request, 'aiboearn_sell_asset_success.html', success_content)
                        else:
                            messages.error(request, 'You do not have enough Available balance to withdraw from!')
                    else:
                        messages.error(request, 'Your AIBO Earn Account has been locked! \nContact User Centre')
            except Exception as e:
                print(e)
                messages.error(request, 'Error occurred')
    else:
        form = AssetSaleForm()

    content = {
        'user': searched_user,
        'user_wallet': user_wallet,
        'aibo': aibo,
        'purchase': purchase,
        'form': form,
        'sales': AssetSales.objects.filter(purchase=purchase_id),
        'assets': Asset.objects.all(),
        'sectors': Sector.objects.all()
    }
    return render(request, 'aiboearn_sell_asset.html', content)

@login_required
@user_access_only()
def purchase_yearly_license(request):
    content = {}
    try:
        if request.method == 'POST':
            return redirect('purchase_yearly_license_complete',permanent=True)
        searched_user = UserProfile.objects.get(email=request.user)
        content['user'] = searched_user
        content['user_wallet'] = AIBOWallet.objects.get(user=searched_user)
        content['aibo'] = AIBO.objects.get(user=searched_user)
        content['yearly'] = AIBORates.objects.latest('created_at').yearly_subscription
    except Exception:
        return render(request, 'op_error_403.html')

    return render(request, 'aiboearn_purchase_yearly_license.html', content)

@login_required
@user_access_only()
def purchase_yearly_license_complete(request):
    try:
        searched_user = UserProfile.objects.get(email=request.user)
        user_wallet = AIBOWallet.objects.get(user=searched_user)
        aiborates = AIBORates.objects.latest('created_at')
        
        with transaction.atomic():
            if user_wallet.balance >= aiborates.yearly_subscription:
                if YearlyLicense.new_purchase(searched_user):
                    user_wallet.balance -= aiborates.yearly_subscription
                    user_wallet.outflow += aiborates.yearly_subscription
                    user_wallet.save()
                    new_transaction = WalletTransaction.objects.create(
                        wallet=user_wallet,
                        transaction_type='Purchase',
                        email=searched_user.email,
                        description='Yearly License Purchase',
                        amount = aiborates.yearly_subscription,
                        status='Success'
                    )
                    new_transaction.save()
                    messages.success(request, 'Purchase Successful')
                    return redirect('user_dashboard')
                else:
                    messages.error(request, 'License not Expired')
                    return redirect('user_dashboard')
            else:
                messages.error(request, 'Insufficient Account Balance')
                return redirect('user_dashboard')

    except Exception as e:
        print("Error in processing the payment", str(e))
        messages.error(request, "An error occurred while processing your request")
        return redirect('user_dashboard')

@login_required
@user_access_only()
def purchase_monthly_license(request):
    content = {}
    try:
        if request.method == 'POST':
            return redirect('purchase_monthly_license_complete',permanent=True)
        searched_user = UserProfile.objects.get(email=request.user)
        content['user'] = searched_user
        content['user_wallet'] = AIBOWallet.objects.get(user=searched_user)
        content['aibo'] = AIBO.objects.get(user=searched_user)
        content['monthly'] = AIBORates.objects.latest('created_at').monthly_subscription
    except Exception as e:
        return render(request, 'op_error_403.html')

    return render(request, 'aiboearn_purchase_monthly_license.html', content)

@login_required
@user_access_only()
def monthly_yearly_license_complete(request):
    searched_user = UserProfile.objects.get(email = request.user)
    user_wallet = AIBOWallet.objects.get(user = searched_user)
    aiborates = AIBORates.objects.latest('created_at')
    try:
        with transaction.atomic():
            if user_wallet.balance >= aiborates.monthly_subscription:
                if MonthlyLicense.new_purchase(searched_user):
                    user_wallet.balance -= aiborates.monthly_subscription
                    user_wallet.outflow += aiborates.monthly_subscription
                    user_wallet.save()
                    new_transaction = WalletTransaction.objects.create(
                        wallet=user_wallet,
                        transaction_type='Purchase',
                        email=searched_user.email,
                        description='Monthly License Purchase',
                        amount = aiborates.monthly_subscription,
                        status='Success'
                    )
                    new_transaction.save()
                    messages.success(request, 'Purchase Successful')
                    return redirect('user_dashboard')
                else:
                    messages.error(request, 'License not Expired')
                    return redirect('user_dashboard')
            else:
                messages.error(request, 'Insufficient Account Balance')
                return redirect('user_dashboard')

    except Exception as e:
        print("Error in processing the payment", str(e))
        messages.error(request, "An error occurred while processing your request")
        return redirect('user_dashboard')
