import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .access import can_direct_message, is_room_member, is_room_muted
from .models import DirectMessage, Message, Notification, Room, User
from .sanitization import sanitize_markdown_source


WS_CLOSE_BAD_REQUEST = 4400
WS_CLOSE_UNAUTHENTICATED = 4401
WS_CLOSE_FORBIDDEN = 4403
WS_CLOSE_NOT_FOUND = 4404

# Global in-memory set of online user IDs (works with InMemoryChannelLayer).
# Shared presence infrastructure is intentionally outside this authorization fix.
ONLINE_USERS = set()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.joined_group = False
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=WS_CLOSE_UNAUTHENTICATED)
            return
        if not user.is_active:
            await self.close(code=WS_CLOSE_FORBIDDEN)
            return

        self.room_id = int(self.scope['url_route']['kwargs']['room_id'])
        access = await self.get_room_access(user.pk, self.room_id)
        if not access['exists']:
            await self.close(code=WS_CLOSE_NOT_FOUND)
            return
        if not access['member']:
            await self.close(code=WS_CLOSE_FORBIDDEN)
            return

        self.room_group_name = f'chat_{self.room_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        self.joined_group = True
        await self.accept()

    async def disconnect(self, close_code):
        if self.joined_group:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            await self.close(code=WS_CLOSE_BAD_REQUEST)
            return

        try:
            data = json.loads(text_data)
        except (TypeError, ValueError):
            await self.close(code=WS_CLOSE_BAD_REQUEST)
            return
        if not isinstance(data, dict):
            await self.close(code=WS_CLOSE_BAD_REQUEST)
            return

        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=WS_CLOSE_UNAUTHENTICATED)
            return

        access = await self.get_room_access(user.pk, self.room_id)
        if not access['exists']:
            await self.close(code=WS_CLOSE_NOT_FOUND)
            return
        if not access['member']:
            await self.close(code=WS_CLOSE_FORBIDDEN)
            return

        event_type = data.get('type', 'message')
        if access['muted']:
            await self.send_error('muted', 'You are muted in this room.')
            return

        if event_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_event',
                    'room_id': self.room_id,
                    'username': user.username,
                    'user_id': user.pk,
                    'is_typing': bool(data.get('is_typing', False)),
                },
            )
            return
        if event_type != 'message':
            await self.send_error('invalid_event', 'Unsupported event type.')
            return

        body = data.get('body', '')
        if not isinstance(body, str) or not body.strip():
            await self.send_error('empty_message', 'Message body is required.')
            return

        result = await self.save_authorized_message(user.pk, self.room_id, body.strip())
        if result['status'] == 'not_found':
            await self.close(code=WS_CLOSE_NOT_FOUND)
            return
        if result['status'] == 'forbidden':
            await self.close(code=WS_CLOSE_FORBIDDEN)
            return
        if result['status'] == 'muted':
            await self.send_error('muted', 'You are muted in this room.')
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'room_id': self.room_id,
                'body': result['body'],
                'username': result['username'],
                'avatar_url': result['avatar_url'],
                'user_id': user.pk,
                'timestamp': 'just now',
            },
        )

    async def chat_message(self, event):
        if int(event.get('room_id', -1)) != self.room_id:
            await self.close(code=WS_CLOSE_FORBIDDEN)
            return
        if not await self.connection_still_authorized():
            return

        await self.send(text_data=json.dumps({
            'type': 'message',
            'body': sanitize_markdown_source(event['body']),
            'username': event['username'],
            'avatar_url': event['avatar_url'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp'],
        }))

    async def typing_event(self, event):
        if int(event.get('room_id', -1)) != self.room_id:
            await self.close(code=WS_CLOSE_FORBIDDEN)
            return
        if not await self.connection_still_authorized():
            return

        await self.send(text_data=json.dumps({
            'type': 'typing',
            'username': event['username'],
            'user_id': event['user_id'],
            'is_typing': event['is_typing'],
        }))

    async def connection_still_authorized(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=WS_CLOSE_UNAUTHENTICATED)
            return False
        access = await self.get_room_access(user.pk, self.room_id)
        if not access['exists']:
            await self.close(code=WS_CLOSE_NOT_FOUND)
            return False
        if not access['member']:
            await self.close(code=WS_CLOSE_FORBIDDEN)
            return False
        return True

    async def send_error(self, code, message):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'code': code,
            'message': message,
        }))

    @database_sync_to_async
    def get_room_access(self, user_id, room_id):
        user = User.objects.filter(pk=user_id, is_active=True).first()
        room = Room.objects.filter(pk=room_id).first()
        if room is None:
            return {'exists': False, 'member': False, 'muted': False}
        if user is None:
            return {'exists': True, 'member': False, 'muted': False}
        return {
            'exists': True,
            'member': is_room_member(user, room),
            'muted': is_room_muted(user, room),
        }

    @database_sync_to_async
    def save_authorized_message(self, user_id, room_id, body):
        user = User.objects.filter(pk=user_id, is_active=True).first()
        room = Room.objects.filter(pk=room_id).first()
        if room is None:
            return {'status': 'not_found'}
        if user is None or not is_room_member(user, room):
            return {'status': 'forbidden'}
        if is_room_muted(user, room):
            return {'status': 'muted'}

        message = Message.objects.create(user=user, room=room, body=body)
        participants = room.participants.exclude(pk=user.pk)
        Notification.objects.bulk_create([
            Notification(
                user=participant,
                notification_type='message',
                message=f'@{user.username} sent a message in "{room.name}"',
                room=room,
                sender=user,
            )
            for participant in participants
        ])
        avatar_url = user.avatar.url if user.avatar else '/static/images/avatar.svg'
        return {
            'status': 'ok',
            'body': sanitize_markdown_source(message.body),
            'username': user.username,
            'avatar_url': avatar_url,
        }


class DMConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.joined_group = False
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=WS_CLOSE_UNAUTHENTICATED)
            return
        if not user.is_active:
            await self.close(code=WS_CLOSE_FORBIDDEN)
            return

        self.other_user_id = int(self.scope['url_route']['kwargs']['user_id'])
        access = await self.get_dm_access(user.pk, self.other_user_id)
        if access['status'] == 'not_found':
            await self.close(code=WS_CLOSE_NOT_FOUND)
            return
        if access['status'] != 'ok':
            await self.close(code=WS_CLOSE_FORBIDDEN)
            return

        self.participant_ids = tuple(access['participant_ids'])
        self.room_group_name = f'dm_{self.participant_ids[0]}_{self.participant_ids[1]}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        self.joined_group = True
        await self.accept()

    async def disconnect(self, close_code):
        if self.joined_group:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            await self.close(code=WS_CLOSE_BAD_REQUEST)
            return
        try:
            data = json.loads(text_data)
        except (TypeError, ValueError):
            await self.close(code=WS_CLOSE_BAD_REQUEST)
            return
        if not isinstance(data, dict):
            await self.close(code=WS_CLOSE_BAD_REQUEST)
            return

        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=WS_CLOSE_UNAUTHENTICATED)
            return

        body = data.get('body', '')
        if not isinstance(body, str) or not body.strip():
            await self.send_error('empty_message', 'Message body is required.')
            return

        result = await self.save_authorized_dm(user.pk, self.other_user_id, body.strip())
        if result['status'] == 'not_found':
            await self.close(code=WS_CLOSE_NOT_FOUND)
            return
        if result['status'] != 'ok':
            await self.close(code=WS_CLOSE_FORBIDDEN)
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'dm_message',
                'body': result['body'],
                'sender_id': user.pk,
                'username': result['username'],
                'avatar_url': result['avatar_url'],
                'timestamp': 'just now',
                'participant_ids': result['participant_ids'],
            },
        )

    async def dm_message(self, event):
        event_participants = tuple(sorted(int(pk) for pk in event.get('participant_ids', [])))
        user = self.scope.get('user')
        if (
            not user
            or not user.is_authenticated
            or event_participants != self.participant_ids
            or user.pk not in event_participants
        ):
            await self.close(code=WS_CLOSE_FORBIDDEN)
            return

        access = await self.get_dm_access(user.pk, self.other_user_id)
        if access['status'] != 'ok':
            close_code = (
                WS_CLOSE_NOT_FOUND
                if access['status'] == 'not_found'
                else WS_CLOSE_FORBIDDEN
            )
            await self.close(code=close_code)
            return

        await self.send(text_data=json.dumps({
            'body': sanitize_markdown_source(event['body']),
            'sender_id': event['sender_id'],
            'username': event['username'],
            'avatar_url': event['avatar_url'],
            'timestamp': event['timestamp'],
        }))

    async def send_error(self, code, message):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'code': code,
            'message': message,
        }))

    @database_sync_to_async
    def get_dm_access(self, user_id, other_user_id):
        user = User.objects.filter(pk=user_id, is_active=True).first()
        other_user = User.objects.filter(pk=other_user_id, is_active=True).first()
        if other_user is None:
            return {'status': 'not_found'}
        if user is None or not can_direct_message(user, other_user):
            return {'status': 'forbidden'}
        return {
            'status': 'ok',
            'participant_ids': sorted([user.pk, other_user.pk]),
        }

    @database_sync_to_async
    def save_authorized_dm(self, sender_id, recipient_id, body):
        sender = User.objects.filter(pk=sender_id, is_active=True).first()
        recipient = User.objects.filter(pk=recipient_id, is_active=True).first()
        if recipient is None:
            return {'status': 'not_found'}
        if sender is None or not can_direct_message(sender, recipient):
            return {'status': 'forbidden'}

        dm = DirectMessage.objects.create(sender=sender, recipient=recipient, body=body)
        Notification.objects.create(
            user=recipient,
            notification_type='message',
            message=f'@{sender.username} sent you a direct message',
            sender=sender,
        )
        avatar_url = sender.avatar.url if sender.avatar else '/static/images/avatar.svg'
        return {
            'status': 'ok',
            'body': sanitize_markdown_source(dm.body),
            'username': sender.username,
            'avatar_url': avatar_url,
            'participant_ids': sorted([sender.pk, recipient.pk]),
        }


class PresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.registered_presence = False
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=WS_CLOSE_UNAUTHENTICATED)
            return
        if not user.is_active or not await self.user_is_active(user.pk):
            await self.close(code=WS_CLOSE_FORBIDDEN)
            return

        self.user_id = user.pk
        ONLINE_USERS.add(self.user_id)
        self.registered_presence = True
        await self.accept()
        await self.send(text_data=json.dumps({
            'online_users': sorted(ONLINE_USERS),
        }))

    async def receive(self, text_data=None, bytes_data=None):
        # Presence identity comes exclusively from the authenticated session.
        # Clients never need to submit a user ID or mutate presence manually.
        await self.close(code=WS_CLOSE_FORBIDDEN)

    async def disconnect(self, close_code):
        if self.registered_presence:
            ONLINE_USERS.discard(self.user_id)

    @database_sync_to_async
    def user_is_active(self, user_id):
        return User.objects.filter(pk=user_id, is_active=True).exists()
