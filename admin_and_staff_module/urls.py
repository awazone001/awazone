from django.urls import path
from . import views

urlpatterns=[
    path('dashboard/',views.admin_dashboard,name='admin_dashboard'),
    path('profile/',views.update_profile, name="admin_profile"),
    path('manage/terms_and_conditions/',views.manage_terms_and_conditions,name='manage_terms_and_conditions'),
    path('staff/',views.view_staffs,name='view_staffs'),
    path('staff/<id>/',views.view_staff,name='view_staff'),
    path('staff/',views.view_staff,name='view_staff'),
    path('ranks',views.admin_view_level,name='admin_view_rank'),
    path('update-ranks',views.add_level,name='update-ranks'),
    path('slides',views.view_slides,name='view_slides'),
    path('create-slide',views.create_slide,name='create_slide'),
    path('delete-slide/<id>',views.delete_slide,name='delete_slide'),
    path('edit-slides/<id>/',views.edit_slide,name='edit_slide'),
]