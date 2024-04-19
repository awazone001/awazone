from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('',views.sign_in,name='user_login'),
    path('signout/',views.sign_out,name='user_logout'),
    path('signup/',views.sign_up,name='user_signup'),
    path('activate/<str:uidb64>/<str:token>/', views.activate, name='activate'),
    path('dashboard/',views.user_dashboard,name='user_dashboard'),
    path('profile/',views.view_profile,name='user_profile'),
    path('update-profile/',views.update_profile,name='update_profile'),
    path('reset-password/',
    auth_views.PasswordResetView.as_view(template_name = "reset_password_email_confirmation.html"),
    name="reset_password"),
    path('reset-password-sent/',
    auth_views.PasswordResetDoneView.as_view(template_name = "reset_password_mail_sent.html"),
    name="password_reset_done"),
    path('reset/<uidb64>/<token>/',
    auth_views.PasswordResetConfirmView.as_view(template_name = "reset_password.html"),
    name="password_reset_confirm"),
    path('reset-password-complete/',
    auth_views.PasswordResetCompleteView.as_view(template_name = "reset_password_done.html"),
    name="password_reset_complete"),
    path('user-ranks/',views.view_rank,name='view_ranks'),
    path('terms-and-conditions/',views.view_terms_and_conditions,name='terms-and-conditions'),
    path('direct-referrals/',views.view_direct_referrals,name='direct-referrals')
]
