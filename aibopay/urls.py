from django.urls import path
from . import views

urlpatterns = [
    #admin manage aibopay urls
    path('admin/manage_rates/',views.manage_rates,name='manage_rates'),
    path('reset-pin/',views.resetpin,name='reset_pin'),
    path('reset-pin/<id>/',views.resetpin_otp_confirmation,name='reset_pin_confirmation'),
    path('resend-otp/',views.resend_otp,name='resend_otp'),
    path('dashboard',views.aibopay_dashboard,name='aibopay_dashboard'),
    path('add-account/', views.add_account, name='verify_account'),
    path('verify-account/<id>/', views.verify_account, name='confirm_account'),
    path('delete-account/<account_number>/', views.delete_account, name='delete_account'),
    path('payout-account/', views.payout_account, name='payout_account'),
    path('deposit/', views.deposit, name='initiate_payment'),
    path('deposit/authenticate_deposit/', views.authenticate_deposit, name='authenticate_deposit'),
    path('withdraw/', views.withdraw, name='withdraw'),
    path('confirm-withdrawal/<ref>/',views.authenticate_PIN,name='pin_confirmation'),
    path('complete-withdrawal/<ref>/', views.complete_withdrawal, name='complete_withdrawal'),
]