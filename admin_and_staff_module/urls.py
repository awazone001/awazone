from django.urls import path
from . import views
# from .views import SlidePhotoListCreateAPIView,SlidePhotoRetrieveUpdateDestroyAPIView

urlpatterns=[
    path('dashboard/',views.admin_dashboard,name='admin_dashboard'),
    path('profile/',views.update_profile, name="admin_profile"),
    path('staff/',views.view_staffs,name='view_staffs'),
    path('staff/<id>/',views.view_staff,name='view_staff'),
    path('staff/',views.view_staff,name='view_staff'),
    path('manage/terms_and_conditions/',views.manage_terms_and_conditions,name='manage_terms_and_conditions'),
    path('levels',views.admin_view_level,name='admin_view_level'),
    path('add_levels',views.add_level,name='add_level'),
    # path('api/slide-photos/', SlidePhotoListCreateAPIView.as_view(), name='slide-photo-list-create'),
    # path('api/slide-photos/<int:pk>/', SlidePhotoRetrieveUpdateDestroyAPIView.as_view(), name='slide-photo-detail'),
]