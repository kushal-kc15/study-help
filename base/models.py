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
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    

class Topic(models.Model):
    name=models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Room(models.Model):
    host = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    topic=models.ForeignKey(Topic,on_delete=models.SET_NULL,null=True,blank=True)
    tags=models.ManyToManyField(Topic,related_name='tagged_rooms',blank=True)
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