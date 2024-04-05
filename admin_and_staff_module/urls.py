from django.urls import path
from . import views

urlpatterns=[
    path('dashboard/',views.admin_dashboard,name='admin_dashboard'),
    path('profile/',views.update_profile, name="admin_profile"),
    path('manage/terms_and_conditions/',views.manage_terms_and_conditions,name='manage_terms_and_conditions'),
    path('ranks',views.admin_view_level,name='admin_view_rank'),
    path('update-ranks',views.add_level,name='update-ranks'),
    path('slides',views.view_slides,name='view_slides'),
    path('create-slide',views.create_slide,name='create_slide'),
    path('delete-slide/<id>',views.delete_slide,name='delete_slide'),
    path('edit-slides/<id>/',views.edit_slide,name='edit_slide'),
    path('view-users-and-staff/',views.view_users,name = 'admin_view_users'),
    path('view-user-profile/<userid>/',views.admin_view_user_profile,name= "admin_view_user" ),
    path('make-staff/<userid>/',views.create_staff,name='make-staff'),
    path('remove-staff/<userid>/',views.remove_staff,name='remove-staff'),
    path('activate-user/<userid>/',views.activate_user,name='activate-user'),
    path('deactivate-user/<userid>/',views.deactivate_user,name='deactivate-user'),
]