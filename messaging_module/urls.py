from django.urls import path,re_path
from . import views

#admin manage aiboearn urls
urlpatterns = [
    path('contact/',views.contact_view,name='contact'),
    path('Customer-support/',views.create_room,name='customer_support'),
    re_path(r'^ws/(?P<room_name>[^/]+)/$', views.room_message_sender, name='room_message_sender'),
    re_path(r'^ws/receiver/(?P<room_name>[^/]+)/$', views.room_message_receiver, name='room_message_receiver'),
    path('admin/chats/',views.rooms,name = 'rooms'),
    path('mark_notification_as_read/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('get_notification',views.get_notifications,name='get_notification')
]