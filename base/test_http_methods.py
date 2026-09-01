import tempfile

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import DirectMessage, Message, MessageReaction, Notification, Room, RoomFile, User


class StateChangingEndpointTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            username='host', email='host@example.com', password='password'
        )
        self.member = User.objects.create_user(
            username='member', email='member@example.com', password='password'
        )
        self.outsider = User.objects.create_user(
            username='outsider', email='outsider@example.com', password='password'
        )
        self.room = Room.objects.create(host=self.host, name='Security room')
        self.room.participants.add(self.member)
        self.message = Message.objects.create(
            user=self.member, room=self.room, body='Safe message'
        )
        self.room_file = RoomFile.objects.create(
            room=self.room,
            uploaded_by=self.member,
            file='room_files/nonexistent-test-file.txt',
            original_name='test.txt',
        )
        self.notification = Notification.objects.create(
            user=self.member,
            notification_type='message',
            message='Unread notification',
            sender=self.host,
        )
        self.direct_message = DirectMessage.objects.create(
            sender=self.host,
            recipient=self.member,
            body='Unread direct message',
        )

    def test_get_is_non_mutating_for_post_only_endpoints(self):
        self.client.force_login(self.member)
        message_count = Message.objects.count()
        dm_count = DirectMessage.objects.count()
        invite_token = self.room.invite_token

        urls = [
            reverse('skip-onboarding'),
            reverse('resend-verification'),
            reverse('upload-room-file', args=[self.room.id]),
            reverse('delete-room-file', args=[self.room_file.id]),
            reverse('toggle-reaction', args=[self.message.id]),
            reverse('join-room', args=[self.room.id]),
            reverse('regenerate-invite', args=[self.room.id]),
            reverse('mute-user', args=[self.room.id, self.member.id]),
            reverse('kick-user', args=[self.room.id, self.member.id]),
            reverse('pin-message', args=[self.room.id, self.message.id]),
            reverse('toggle-bookmark', args=[self.room.id]),
            reverse('mark-notifications-read'),
            reverse('mark-dm-read', args=[self.host.id]),
            reverse('send-room-message', args=[self.room.id]),
            reverse('send-dm-message', args=[self.host.id]),
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 405)

        self.member.refresh_from_db()
        self.room.refresh_from_db()
        self.notification.refresh_from_db()
        self.direct_message.refresh_from_db()
        self.assertFalse(self.member.onboarding_complete)
        self.assertEqual(self.room.invite_token, invite_token)
        self.assertTrue(self.room.participants.filter(id=self.member.id).exists())
        self.assertFalse(self.room.muted_users.filter(id=self.member.id).exists())
        self.assertIsNone(self.room.pinned_message_id)
        self.assertFalse(self.room.bookmarked_by.filter(id=self.member.id).exists())
        self.assertTrue(RoomFile.objects.filter(id=self.room_file.id).exists())
        self.assertFalse(MessageReaction.objects.exists())
        self.assertFalse(self.notification.is_read)
        self.assertFalse(self.direct_message.is_read)
        self.assertEqual(Message.objects.count(), message_count)
        self.assertEqual(DirectMessage.objects.count(), dm_count)
        self.assertEqual(len(mail.outbox), 0)

    def test_confirmation_gets_do_not_verify_or_join(self):
        self.client.force_login(self.outsider)

        verify_response = self.client.get(
            reverse('verify-email', args=[self.outsider.email_verification_token])
        )
        invite_response = self.client.get(
            reverse('join-invite', args=[self.room.invite_token])
        )

        self.outsider.refresh_from_db()
        self.assertEqual(verify_response.status_code, 200)
        self.assertEqual(invite_response.status_code, 200)
        self.assertFalse(self.outsider.is_email_verified)
        self.assertFalse(self.room.participants.filter(id=self.outsider.id).exists())
        self.assertContains(verify_response, 'method="POST"')
        self.assertContains(invite_response, 'method="POST"')
        self.assertContains(verify_response, 'csrfmiddlewaretoken')
        self.assertContains(invite_response, 'csrfmiddlewaretoken')

    def test_read_only_notification_and_dm_gets_do_not_mark_read(self):
        self.client.force_login(self.member)

        self.assertEqual(self.client.get(reverse('notifications')).status_code, 200)
        self.assertEqual(self.client.get(reverse('dm', args=[self.host.id])).status_code, 200)
        poll_url = reverse('poll-dm-messages', args=[self.host.id]) + '?after=0'
        self.assertEqual(self.client.get(poll_url).status_code, 200)

        self.notification.refresh_from_db()
        self.direct_message.refresh_from_db()
        self.assertFalse(self.notification.is_read)
        self.assertFalse(self.direct_message.is_read)

    def test_authorized_posts_update_state(self):
        self.client.force_login(self.member)

        self.assertEqual(self.client.post(reverse('skip-onboarding')).status_code, 302)
        self.assertEqual(
            self.client.post(reverse('toggle-bookmark', args=[self.room.id])).status_code,
            302,
        )
        reaction_response = self.client.post(
            reverse('toggle-reaction', args=[self.message.id]),
            {'emoji': MessageReaction.EMOJIS[0]},
        )
        self.assertEqual(reaction_response.status_code, 200)
        self.assertEqual(self.client.post(reverse('mark-notifications-read')).status_code, 200)
        self.assertEqual(
            self.client.post(reverse('mark-dm-read', args=[self.host.id])).status_code,
            200,
        )
        self.assertEqual(self.client.post(reverse('resend-verification')).status_code, 302)

        self.member.refresh_from_db()
        self.notification.refresh_from_db()
        self.direct_message.refresh_from_db()
        self.assertTrue(self.member.onboarding_complete)
        self.assertTrue(self.room.bookmarked_by.filter(id=self.member.id).exists())
        self.assertTrue(MessageReaction.objects.filter(message=self.message, user=self.member).exists())
        self.assertTrue(self.notification.is_read)
        self.assertTrue(self.direct_message.is_read)
        self.assertEqual(len(mail.outbox), 1)

    def test_verification_and_invite_mutate_only_on_post(self):
        self.client.force_login(self.outsider)

        self.assertEqual(
            self.client.post(
                reverse('verify-email', args=[self.outsider.email_verification_token])
            ).status_code,
            302,
        )
        self.assertEqual(
            self.client.post(reverse('join-invite', args=[self.room.invite_token])).status_code,
            302,
        )

        self.outsider.refresh_from_db()
        self.assertTrue(self.outsider.is_email_verified)
        self.assertTrue(self.room.participants.filter(id=self.outsider.id).exists())

    def test_host_moderation_and_deletion_require_post(self):
        self.client.force_login(self.host)
        old_token = self.room.invite_token

        self.assertEqual(
            self.client.post(reverse('mute-user', args=[self.room.id, self.member.id])).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(reverse('pin-message', args=[self.room.id, self.message.id])).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(reverse('regenerate-invite', args=[self.room.id])).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(reverse('delete-room-file', args=[self.room_file.id])).status_code,
            302,
        )

        self.room.refresh_from_db()
        self.assertTrue(self.room.muted_users.filter(id=self.member.id).exists())
        self.assertEqual(self.room.pinned_message_id, self.message.id)
        self.assertNotEqual(self.room.invite_token, old_token)
        self.assertFalse(RoomFile.objects.filter(id=self.room_file.id).exists())

        self.assertEqual(
            self.client.post(reverse('kick-user', args=[self.room.id, self.member.id])).status_code,
            200,
        )
        self.assertFalse(self.room.participants.filter(id=self.member.id).exists())
        self.assertFalse(self.room.muted_users.filter(id=self.member.id).exists())

    def test_existing_delete_confirmation_gets_are_non_mutating(self):
        extra_room = Room.objects.create(host=self.host, name='Delete me')
        extra_message = Message.objects.create(user=self.host, room=self.room, body='Delete me')
        self.client.force_login(self.host)

        self.assertEqual(
            self.client.get(reverse('delete-room', args=[extra_room.id])).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse('delete-message', args=[extra_message.id])).status_code,
            200,
        )
        self.assertTrue(Room.objects.filter(id=extra_room.id).exists())
        self.assertTrue(Message.objects.filter(id=extra_message.id).exists())

        self.assertEqual(
            self.client.post(reverse('delete-room', args=[extra_room.id])).status_code,
            302,
        )
        self.assertEqual(
            self.client.post(reverse('delete-message', args=[extra_message.id])).status_code,
            302,
        )
        self.assertFalse(Room.objects.filter(id=extra_room.id).exists())
        self.assertFalse(Message.objects.filter(id=extra_message.id).exists())

    def test_unauthorized_users_cannot_modify_room_resources(self):
        self.client.force_login(self.outsider)
        old_token = self.room.invite_token

        forbidden_posts = [
            (reverse('regenerate-invite', args=[self.room.id]), {}),
            (reverse('mute-user', args=[self.room.id, self.member.id]), {}),
            (reverse('kick-user', args=[self.room.id, self.member.id]), {}),
            (reverse('pin-message', args=[self.room.id, self.message.id]), {}),
            (reverse('toggle-reaction', args=[self.message.id]), {'emoji': MessageReaction.EMOJIS[0]}),
            (reverse('upload-room-file', args=[self.room.id]), {}),
            (reverse('delete-room-file', args=[self.room_file.id]), {}),
            (reverse('delete-room', args=[self.room.id]), {}),
            (reverse('delete-message', args=[self.message.id]), {}),
        ]
        for url, data in forbidden_posts:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, data).status_code, 403)

        self.room.refresh_from_db()
        self.assertEqual(self.room.invite_token, old_token)
        self.assertTrue(self.room.participants.filter(id=self.member.id).exists())
        self.assertFalse(self.room.muted_users.filter(id=self.member.id).exists())
        self.assertIsNone(self.room.pinned_message_id)
        self.assertFalse(MessageReaction.objects.exists())
        self.assertTrue(RoomFile.objects.filter(id=self.room_file.id).exists())
        self.assertTrue(Room.objects.filter(id=self.room.id).exists())
        self.assertTrue(Message.objects.filter(id=self.message.id).exists())

    def test_host_cannot_moderate_nonparticipants_or_self(self):
        self.client.force_login(self.host)
        for endpoint, target in (
            ('mute-user', self.outsider),
            ('kick-user', self.outsider),
            ('mute-user', self.host),
            ('kick-user', self.host),
        ):
            with self.subTest(endpoint=endpoint, target=target.username):
                response = self.client.post(
                    reverse(endpoint, args=[self.room.id, target.id])
                )
                self.assertEqual(response.status_code, 403)

    def test_anonymous_users_are_rejected_from_mutations(self):
        protected_urls = [
            reverse('skip-onboarding'),
            reverse('resend-verification'),
            reverse('join-room', args=[self.room.id]),
            reverse('toggle-bookmark', args=[self.room.id]),
            reverse('delete-room-file', args=[self.room_file.id]),
            reverse('mute-user', args=[self.room.id, self.member.id]),
            reverse('mark-notifications-read'),
            reverse('mark-dm-read', args=[self.host.id]),
        ]
        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.post(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn('/login', response.url)

        invite_response = self.client.post(
            reverse('join-invite', args=[self.room.invite_token])
        )
        self.assertEqual(invite_response.status_code, 302)
        self.assertIn('/login', invite_response.url)
        self.assertFalse(self.room.participants.filter(id=self.outsider.id).exists())

    def test_csrf_is_required_and_template_posts_are_compatible(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.member)
        bookmark_url = reverse('toggle-bookmark', args=[self.room.id])

        self.assertEqual(csrf_client.post(bookmark_url).status_code, 403)

        room_response = csrf_client.get(reverse('room', args=[self.room.id]))
        self.assertEqual(room_response.status_code, 200)
        self.assertContains(room_response, f'action="{bookmark_url}"')
        self.assertContains(room_response, 'name="csrfmiddlewaretoken"')
        csrf_token = csrf_client.cookies['csrftoken'].value
        self.assertEqual(
            csrf_client.post(bookmark_url, HTTP_X_CSRFTOKEN=csrf_token).status_code,
            302,
        )
        self.assertTrue(self.room.bookmarked_by.filter(id=self.member.id).exists())

        notifications_response = csrf_client.get(reverse('notifications'))
        self.assertContains(notifications_response, reverse('mark-notifications-read'))
        inbox_response = csrf_client.get(reverse('dm', args=[self.host.id]))
        self.assertContains(inbox_response, reverse('mark-dm-read', args=[self.host.id]))
        onboarding_response = csrf_client.get(reverse('onboarding'))
        self.assertContains(onboarding_response, reverse('skip-onboarding'))

        csrf_client.logout()
        login_response = csrf_client.get(reverse('login'))
        oauth_url = reverse('google-oauth2-begin')
        self.assertContains(login_response, f'action="{oauth_url}"')
        self.assertContains(login_response, 'name="csrfmiddlewaretoken"', count=2)

        csrf_client_without_cookie = Client(enforce_csrf_checks=True)
        self.assertEqual(csrf_client_without_cookie.post(oauth_url).status_code, 403)

    def test_authorized_member_can_upload_file(self):
        self.client.force_login(self.member)
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse('upload-room-file', args=[self.room.id]),
                    {'file': SimpleUploadedFile('notes.txt', b'safe notes')},
                )
                self.assertEqual(response.status_code, 302)
                self.assertTrue(
                    RoomFile.objects.filter(
                        room=self.room,
                        uploaded_by=self.member,
                        original_name='notes.txt',
                    ).exists()
                )
