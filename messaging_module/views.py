from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification,ChatRoom,ChatMessage
from .forms import ContactForm
from user_module.models import UserProfile,AIBO
from user_module.decorators import staff_access_only
from aibopay.models import AIBOWallet,MonthlyLicense,YearlyLicense
from django.core.exceptions import PermissionDenied
from user_module.views import RetrieveUser

@login_required
def get_notifications(request):
    try:
        unread_notifications = Notification.objects.filter(Q(user=request.user) & Q(is_read=False)).order_by('-created_at')
        
        data = {
            'unread_notifications': list(unread_notifications.values()),
            'unread_count' : unread_notifications.count()
        }
        return JsonResponse(data)
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error in get_notifications: {e}")
        # You may choose to raise PermissionDenied or return a specific error message
        raise PermissionDenied("Unable to retrieve notifications")

@login_required
@require_POST
def mark_notification_as_read(request):
    try:
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        notifications.update(is_read=True)

        # Get the referer URL
        referer_url = request.META.get('HTTP_REFERER')

        return JsonResponse({'status': 'success', 'referer': referer_url})
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error in mark_notification_as_read: {e}")
        # You may choose to raise PermissionDenied or return a specific error message
        return JsonResponse({'status': 'error', 'message': 'Internal server error'})

@login_required
def create_room(request):
    chats = ChatRoom.objects.create(user = request.user)
    new_chat = chats.save()
    Notification.notify_all_staff(message=f'message from {request.user}',sender=request.user)
    return redirect('room_message_sender',new_chat,permanent=True)

@login_required
def room_message_sender(request, room_name):
    searched_user = UserProfile.objects.get(email=request.user)

    chatroom = ChatRoom.objects.get(name = room_name)
    chat_messages = ChatMessage.objects.filter(room=chatroom).order_by('timestamp')

    def send_websocket_message(room_group_name, sender, message):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'chat.message',
                'message': message,
                'sender': sender,
            }
        )

    if request.method == 'POST':
        sender = searched_user
        message = request.POST['message']
        ChatMessage.objects.create(sender=sender, content=message, room=chatroom)
        # Send the message via WebSocket to the room group
        send_websocket_message(room_name, sender, message)

    content = {
        'data' : RetrieveUser(request=request,email=request.user.email),
        'room_name': room_name,
        'chat_messages': chat_messages
    }
    return render(request, 'chat.html', content)

@login_required
def room_message_receiver(request, room_name):
    searched_user = UserProfile.objects.get(id=request.user)

    chatroom = ChatRoom.objects.get(name = room_name)
    chat_messages = ChatMessage.objects.filter(room=chatroom).order_by('timestamp')

    def send_websocket_message(room_group_name, sender, message):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'chat.message',
                'message': message,
                'sender': sender,
            }
        )

    if request.method == 'POST':
        sender = searched_user
        message = request.POST['message']
        ChatMessage.objects.create(sender=sender, content=message, room=chatroom)
        # Send the message via WebSocket to the room group
        send_websocket_message(room_name, sender, message)

    content = {
        'user': UserProfile.objects.get(id = request.user),
        'users': UserProfile.objects.exclude(is_staff = True),
        'staff': UserProfile.objects.exclude(is_user = True),
        'notifications' : Notification.objects.filter(Q(user = request.user) & Q(is_read = False)),
        'room_name': chatroom,
        'chat_messages': chat_messages,
        'chat_user': UserProfile.objects.get(id = chatroom.user)
    }
    return render(request, 'admin/room.html', content)

@login_required
@staff_access_only()
def rooms(request):

    chat_rooms = ChatRoom.objects.all()

    content = {
        'user': UserProfile.objects.get(id = request.user),
        'users': UserProfile.objects.exclude(is_staff = True),
        'staff': UserProfile.objects.exclude(is_user = True),
        'notifications' : Notification.objects.filter(Q(user = request.user) & Q(is_read = False)),
        'chat_rooms': chat_rooms
    }
    return render(request, 'admin/rooms.html', content)

@login_required
def contact_view(request):
    searched_user = UserProfile.objects.get(id=request.user)
    form_class = ContactForm
    content = {
        'data' : RetrieveUser(request=request,email=request.user.email),
        'form': form_class
    }
    
    if request.method == 'POST':
        form = form_class(request.POST)

        if form.is_valid():
            template = get_template('user/contact_template.txt')
            context = {
                'contact_first_name': searched_user.first_name,
                'contact_last_name':  searched_user.last_name,
                'contact_email': searched_user.email,
                'subject': form.cleaned_data['subject'].replace('\n', ''),
                'form_content': form.cleaned_data['content'].replace('\n', ''),
            }
            mail_content = template.render(context)
            
            email = EmailMessage(
                subject=form.cleaned_data['subject'].replace('\n', ''),
                body=mail_content,
                from_email=settings.EMAIL_HOST_USER,
                to=[settings.EMAIL_HOST_USER],
                reply_to=[searched_user.email]
            )
            email.content_subtype = 'html'
            email.send()
            messages.success(request,'Thank you for contacting us, we will revert back to you shortly!')
            return redirect('contact', permanent=True)
    
    return render(request, 'user/contact_form.html', content)