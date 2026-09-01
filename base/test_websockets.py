from unittest.mock import AsyncMock

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.conf import settings
from django.test import Client, SimpleTestCase, TransactionTestCase

from studyhelp.asgi import application

from .consumers import (
    DMConsumer,
    ONLINE_USERS,
    WS_CLOSE_FORBIDDEN,
    WS_CLOSE_NOT_FOUND,
    WS_CLOSE_UNAUTHENTICATED,
)
from .models import DirectMessage, Message, Room, User


VALID_ORIGIN = b'https://allowed.example'
INVALID_ORIGIN = b'https://foreign.example'


class WebSocketAuthorizationTests(TransactionTestCase):
    def setUp(self):
        ONLINE_USERS.clear()
        self.host = User.objects.create_user(
            username='host',
            email='host@example.com',
            password='test-password',
        )
        self.member = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='test-password',
        )
        self.other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='test-password',
        )
        self.outsider = User.objects.create_user(
            username='outsider',
            email='outsider@example.com',
            password='test-password',
        )
        self.room = Room.objects.create(host=self.host, name='Authorized room')
        self.room.participants.add(self.member)
        self.session_cookies = {
            user.pk: self.session_cookie(user)
            for user in (self.host, self.member, self.other_user, self.outsider)
        }

    def tearDown(self):
        ONLINE_USERS.clear()

    def session_cookie(self, user):
        client = Client()
        client.force_login(user)
        value = client.cookies[settings.SESSION_COOKIE_NAME].value
        return f'{settings.SESSION_COOKIE_NAME}={value}'.encode()

    def websocket(self, path, user=None, origin=VALID_ORIGIN):
        headers = [(b'origin', origin)]
        if user is not None:
            headers.append((b'cookie', self.session_cookies[user.pk]))
        return WebsocketCommunicator(application, path, headers=headers)

    def test_anonymous_room_connection_is_rejected(self):
        async def scenario():
            communicator = self.websocket(f'/ws/room/{self.room.pk}/')
            connected, close_code = await communicator.connect()
            self.assertFalse(connected)
            self.assertEqual(close_code, WS_CLOSE_UNAUTHENTICATED)

        async_to_sync(scenario)()

    def test_authorized_room_member_connection_is_allowed(self):
        async def scenario():
            communicator = self.websocket(
                f'/ws/room/{self.room.pk}/',
                user=self.member,
            )
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            await communicator.disconnect()

        async_to_sync(scenario)()

    def test_unauthorized_room_user_is_rejected(self):
        async def scenario():
            communicator = self.websocket(
                f'/ws/room/{self.room.pk}/',
                user=self.outsider,
            )
            connected, close_code = await communicator.connect()
            self.assertFalse(connected)
            self.assertEqual(close_code, WS_CLOSE_FORBIDDEN)

        async_to_sync(scenario)()

    def test_missing_room_is_rejected(self):
        async def scenario():
            communicator = self.websocket('/ws/room/999999/', user=self.member)
            connected, close_code = await communicator.connect()
            self.assertFalse(connected)
            self.assertEqual(close_code, WS_CLOSE_NOT_FOUND)

        async_to_sync(scenario)()

    def test_muted_member_can_connect_but_cannot_send_or_type(self):
        self.room.muted_users.add(self.member)

        async def scenario():
            communicator = self.websocket(
                f'/ws/room/{self.room.pk}/',
                user=self.member,
            )
            connected, _ = await communicator.connect()
            self.assertTrue(connected)

            await communicator.send_json_to({'type': 'message', 'body': 'blocked'})
            error = await communicator.receive_json_from()
            self.assertEqual(error['type'], 'error')
            self.assertEqual(error['code'], 'muted')

            await communicator.send_json_to({'type': 'typing', 'is_typing': True})
            typing_error = await communicator.receive_json_from()
            self.assertEqual(typing_error['code'], 'muted')

            count = await database_sync_to_async(Message.objects.count)()
            self.assertEqual(count, 0)
            await communicator.disconnect()

        async_to_sync(scenario)()

    def test_kicked_member_is_blocked_before_message_creation(self):
        async def scenario():
            communicator = self.websocket(
                f'/ws/room/{self.room.pk}/',
                user=self.member,
            )
            connected, _ = await communicator.connect()
            self.assertTrue(connected)

            def remove_membership():
                room = Room.objects.get(pk=self.room.pk)
                room.participants.remove(self.member.pk)

            await database_sync_to_async(remove_membership)()
            await communicator.send_json_to({'type': 'message', 'body': 'blocked'})
            output = await communicator.receive_output()
            self.assertEqual(output['type'], 'websocket.close')
            self.assertEqual(output['code'], WS_CLOSE_FORBIDDEN)

            count = await database_sync_to_async(Message.objects.count)()
            self.assertEqual(count, 0)

        async_to_sync(scenario)()

    def test_authorized_room_message_is_created(self):
        async def scenario():
            communicator = self.websocket(
                f'/ws/room/{self.room.pk}/',
                user=self.member,
            )
            connected, _ = await communicator.connect()
            self.assertTrue(connected)

            await communicator.send_json_to({'type': 'message', 'body': 'allowed'})
            event = await communicator.receive_json_from()
            self.assertEqual(event['type'], 'message')
            self.assertEqual(event['body'], 'allowed')
            count = await database_sync_to_async(Message.objects.count)()
            self.assertEqual(count, 1)
            await communicator.disconnect()

        async_to_sync(scenario)()

    def test_authorized_dm_participant_is_allowed(self):
        async def scenario():
            communicator = self.websocket(
                f'/ws/dm/{self.other_user.pk}/',
                user=self.member,
            )
            connected, _ = await communicator.connect()
            self.assertTrue(connected)

            await communicator.send_json_to({'body': 'private message'})
            event = await communicator.receive_json_from()
            self.assertEqual(event['body'], 'private message')
            count = await database_sync_to_async(DirectMessage.objects.count)()
            self.assertEqual(count, 1)
            await communicator.disconnect()

        async_to_sync(scenario)()

    def test_anonymous_dm_connection_is_rejected(self):
        async def scenario():
            communicator = self.websocket(f'/ws/dm/{self.other_user.pk}/')
            connected, close_code = await communicator.connect()
            self.assertFalse(connected)
            self.assertEqual(close_code, WS_CLOSE_UNAUTHENTICATED)

        async_to_sync(scenario)()

    def test_unrelated_user_cannot_receive_foreign_dm_conversation(self):
        async def scenario():
            member_dm = self.websocket(
                f'/ws/dm/{self.other_user.pk}/',
                user=self.member,
            )
            outsider_dm = self.websocket(
                f'/ws/dm/{self.other_user.pk}/',
                user=self.outsider,
            )
            member_connected, _ = await member_dm.connect()
            outsider_connected, _ = await outsider_dm.connect()
            self.assertTrue(member_connected)
            self.assertTrue(outsider_connected)

            await member_dm.send_json_to({'body': 'member/other only'})
            await member_dm.receive_json_from()
            self.assertTrue(await outsider_dm.receive_nothing(timeout=0.1))

            await member_dm.disconnect()
            await outsider_dm.disconnect()

        async_to_sync(scenario)()

    def test_self_dm_connection_is_rejected(self):
        async def scenario():
            communicator = self.websocket(
                f'/ws/dm/{self.member.pk}/',
                user=self.member,
            )
            connected, close_code = await communicator.connect()
            self.assertFalse(connected)
            self.assertEqual(close_code, WS_CLOSE_FORBIDDEN)

        async_to_sync(scenario)()

    def test_foreign_origin_is_rejected(self):
        async def scenario():
            communicator = self.websocket(
                f'/ws/room/{self.room.pk}/',
                user=self.member,
                origin=INVALID_ORIGIN,
            )
            connected, _ = await communicator.connect()
            self.assertFalse(connected)

        async_to_sync(scenario)()

    def test_valid_configured_origin_is_accepted(self):
        async def scenario():
            communicator = self.websocket(
                f'/ws/room/{self.room.pk}/',
                user=self.member,
                origin=VALID_ORIGIN,
            )
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            await communicator.disconnect()

        async_to_sync(scenario)()

    def test_presence_uses_authenticated_identity_and_rejects_client_updates(self):
        async def scenario():
            communicator = self.websocket('/ws/presence/', user=self.member)
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            initial = await communicator.receive_json_from()
            self.assertIn(self.member.pk, initial['online_users'])
            self.assertNotIn(self.outsider.pk, initial['online_users'])

            await communicator.send_json_to({'user_id': self.outsider.pk})
            output = await communicator.receive_output()
            self.assertEqual(output['type'], 'websocket.close')
            self.assertEqual(output['code'], WS_CLOSE_FORBIDDEN)
            self.assertNotIn(self.outsider.pk, ONLINE_USERS)

        async_to_sync(scenario)()

    def test_anonymous_presence_connection_is_rejected(self):
        async def scenario():
            communicator = self.websocket('/ws/presence/')
            connected, close_code = await communicator.connect()
            self.assertFalse(connected)
            self.assertEqual(close_code, WS_CLOSE_UNAUTHENTICATED)

        async_to_sync(scenario)()


class DirectMessageEventAuthorizationTests(SimpleTestCase):
    async def test_unrelated_consumer_is_closed_for_foreign_dm_event(self):
        outsider = type('UserScope', (), {
            'pk': 3,
            'is_authenticated': True,
        })()
        consumer = DMConsumer()
        consumer.scope = {'user': outsider}
        consumer.other_user_id = 2
        consumer.participant_ids = (2, 3)
        consumer.close = AsyncMock()
        consumer.send = AsyncMock()

        await consumer.dm_message({
            'body': 'foreign message',
            'sender_id': 1,
            'username': 'member',
            'avatar_url': '/media/avatar.svg',
            'timestamp': 'just now',
            'participant_ids': [1, 2],
        })

        consumer.close.assert_awaited_once_with(code=WS_CLOSE_FORBIDDEN)
        consumer.send.assert_not_awaited()
