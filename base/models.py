import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator

class User(AbstractUser):
    name=models.CharField(max_length=100,null=True)
    email=models.EmailField(unique=True,max_length=100)
    bio=models.TextField(null=True)
    avatar=models.ImageField(
        null=True,
        default="avatar.svg",
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])],
    )
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    BADGE_DEFINITIONS = [
        {'id': 'newcomer',    'label': 'Newcomer',     'emoji': '🌱', 'desc': 'Joined StudyHelp',           'color': '#22c55e'},
        {'id': 'verified',    'label': 'Verified',     'emoji': '✅', 'desc': 'Verified email address',     'color': '#3b82f6'},
        {'id': 'host',        'label': 'Room Host',    'emoji': '🏠', 'desc': 'Created at least 1 room',    'color': '#8b5cf6'},
        {'id': 'regular',     'label': 'Regular',      'emoji': '💬', 'desc': 'Sent 10+ messages',          'color': '#f59e0b'},
        {'id': 'contributor', 'label': 'Contributor',  'emoji': '🔥', 'desc': 'Sent 50+ messages',          'color': '#ef4444'},
        {'id': 'popular',     'label': 'Popular',      'emoji': '⭐', 'desc': 'Joined 5+ rooms',            'color': '#f97316'},
        {'id': 'sharer',      'label': 'Sharer',       'emoji': '📎', 'desc': 'Shared at least 1 file',     'color': '#06b6d4'},
        {'id': 'veteran',     'label': 'Veteran',      'emoji': '🏆', 'desc': 'Created 5+ rooms',           'color': '#eab308'},
    ]

    def get_badges(self):
        badges = []
        msg_count = self.message_set.count()
        room_count = self.room_set.count()
        joined_count = self.participants.count()
        has_files = self.roomfile_set.exists()

        for b in self.BADGE_DEFINITIONS:
            earned = False
            if b['id'] == 'newcomer':
                earned = True
            elif b['id'] == 'verified':
                earned = self.is_email_verified
            elif b['id'] == 'host':
                earned = room_count >= 1
            elif b['id'] == 'regular':
                earned = msg_count >= 10
            elif b['id'] == 'contributor':
                earned = msg_count >= 50
            elif b['id'] == 'popular':
                earned = joined_count >= 5
            elif b['id'] == 'sharer':
                earned = has_files
            elif b['id'] == 'veteran':
                earned = room_count >= 5
            if earned:
                badges.append(b)
        return badges
    

class Topic(models.Model):
    name=models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Room(models.Model):
    host = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    topic=models.ForeignKey(Topic,on_delete=models.SET_NULL,null=True,blank=True)
    tags=models.ManyToManyField(Topic,related_name='tagged_rooms',blank=True)
    bookmarked_by=models.ManyToManyField(User,related_name='bookmarked_rooms',blank=True)
    muted_users=models.ManyToManyField(User,related_name='muted_in_rooms',blank=True)
    pinned_message=models.OneToOneField('Message',on_delete=models.SET_NULL,null=True,blank=True,related_name='pinned_in_room')
    invite_token=models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    name=models.CharField(max_length=100)
    description=models.TextField(null=True,blank=True)
    participants=models.ManyToManyField(User,related_name='participants',blank=True)
    updated=models.DateTimeField(auto_now=True)
    created=models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering=['-updated','-created']
    
    def __str__(self):
        return self.name
    
class Message(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    room=models.ForeignKey(Room, on_delete=models.CASCADE)
    body=models.TextField()
    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)

    class Meta:
        ordering=['-updated','-created']

    def __str__(self):
        return self.body[0:50]


def room_file_path(instance, filename):
    return f'room_files/{instance.room.id}/{filename}'


class RoomFile(models.Model):
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='files')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to=room_file_path,
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'txt', 'py', 'js', 'html', 'css', 'md', 'zip']
        )]
    )
    original_name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def is_image(self):
        return self.original_name.lower().rsplit('.', 1)[-1] in ('jpg', 'jpeg', 'png', 'gif', 'webp')

    def __str__(self):
        return self.original_name


class MessageReaction(models.Model):
    EMOJIS = ['👍', '❤️', '😂', '🔥', '👀', '🎉']
    message = models.ForeignKey('Message', on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)

    class Meta:
        unique_together = ('message', 'user', 'emoji')

    def __str__(self):
        return f"{self.user.username} {self.emoji} on msg {self.message.id}"


class DirectMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_dms')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_dms')
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return f"{self.sender} → {self.recipient}: {self.body[:40]}"


class Notification(models.Model):
    TYPES = (
        ('message', 'New Message'),
        ('room_invite', 'Room Invite'),
        ('room_created', 'Room Created'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPES)
    message = models.TextField()
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='sent_notifications')
    is_read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"{self.notification_type}: {self.message[:30]}"