from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import UserProfile,Notification
import tracemalloc


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def notify_receiver(self, message, sender):
        tracemalloc.start()
        # Determine the receiver(s) based on your logic
        receivers = [user.username for user in UserProfile.objects.all()]

        # Send a notification to each receiver
        for receiver in receivers:
            if receiver != sender:
                await Notification.notify_all_staff(message=message,sender=sender)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']

        # Get the sender's username
        sender = self.scope['user'].username

        # Handle the received message (e.g., save it to the database, etc.)

        # Send the processed message back to all participants in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender,
            }
        )

        # Notify the receiver(s) about the new message
        await self.notify_receiver(message, sender)


    async def chat_message(self, event):
        message = event['message']

        # Send the chat message to the WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    async def new_message_notification(self, event):
        message = event['message']
        sender = event['sender']

        # Send the notification to the receiver(s)
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': message,
            'sender': sender,
        }))
