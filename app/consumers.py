import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, Booking, User
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.booking_id = self.scope['url_route']['kwargs']['booking_id']
        self.room_group_name = f'chat_{self.booking_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        receiver_id = text_data_json['receiver_id']
        sender = self.scope['user']

        await self.save_message(sender, receiver_id, message)

        # FIX: Added 'sender_id' here
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_name': sender.full_name,
                'sender_id': sender.id,  # <--- NEW
                'timestamp': timezone.now().strftime('%I:%M %p')
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender_name = event['sender_name']
        sender_id = event['sender_id'] # <--- NEW
        timestamp = event['timestamp']

        # FIX: Sending sender_id to frontend
        await self.send(text_data=json.dumps({
            'message': message,
            'sender_name': sender_name,
            'sender_id': sender_id, # <--- NEW
            'timestamp': timestamp
        }))

    @database_sync_to_async
    def save_message(self, sender, receiver_id, message):
        receiver = User.objects.get(id=receiver_id)
        booking = Booking.objects.get(id=self.booking_id)
        Message.objects.create(
            booking=booking,
            sender=sender,
            receiver=receiver,
            content=message
        )