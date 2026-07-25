import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Message, User, Notification, DirectMessage

# Global in-memory set of online user IDs (works with InMemoryChannelLayer)
ONLINE_USERS = set()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

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
        data = json.loads(text_data)
        body = data['body']
        user = self.scope['user']

        if user.is_anonymous:
            return

        message = await self.save_message(user, self.room_id, body)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'body': body,
                'username': user.username,
                'avatar_url': await self.get_avatar_url(user),
                'user_id': user.id,
                'timestamp': 'just now',
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'body': event['body'],
            'username': event['username'],
            'avatar_url': event['avatar_url'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def save_message(self, user, room_id, body):
        room = Room.objects.get(id=room_id)
        message = Message.objects.create(user=user, room=room, body=body)
        room.participants.add(user)
        participants = room.participants.exclude(id=user.id)
        notifications = [
            Notification(
                user=participant,
                notification_type='message',
                message=f"@{user.username} sent a message in \"{room.name}\"",
                room=room,
                sender=user,
            )
            for participant in participants
        ]
        Notification.objects.bulk_create(notifications)
        return message

    @database_sync_to_async
    def get_avatar_url(self, user):
        return user.avatar.url if user.avatar else '/static/images/avatar.svg'


class DMConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            await self.close()
            return
        other_id = self.scope['url_route']['kwargs']['user_id']
        ids = sorted([user.id, int(other_id)])
        self.room_group_name = f'dm_{ids[0]}_{ids[1]}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        body = data.get('body', '').strip()
        user = self.scope['user']
        other_id = self.scope['url_route']['kwargs']['user_id']

        if not body or user.is_anonymous:
            return

        dm, avatar_url = await self.save_dm(user, other_id, body)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'dm_message',
                'body': body,
                'sender_id': user.id,
                'username': user.username,
                'avatar_url': avatar_url,
                'timestamp': 'just now',
            }
        )

    async def dm_message(self, event):
        await self.send(text_data=json.dumps({
            'body': event['body'],
            'sender_id': event['sender_id'],
            'username': event['username'],
            'avatar_url': event['avatar_url'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def save_dm(self, sender, recipient_id, body):
        recipient = User.objects.get(id=recipient_id)
        dm = DirectMessage.objects.create(sender=sender, recipient=recipient, body=body)
        Notification.objects.create(
            user=recipient,
            notification_type='message',
            message=f"@{sender.username} sent you a direct message",
            sender=sender,
        )
        avatar_url = sender.avatar.url if sender.avatar else '/static/images/avatar.svg'
        return dm, avatar_url


class PresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            await self.close()
            return
        self.user_id = user.id
        ONLINE_USERS.add(self.user_id)
        await self.accept()
        await self.send(text_data=json.dumps({
            'online_users': list(ONLINE_USERS)
        }))

    async def disconnect(self, close_code):
        ONLINE_USERS.discard(getattr(self, 'user_id', None))
