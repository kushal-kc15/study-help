import uuid
from django.db import migrations, models


def set_unique_tokens(apps, schema_editor):
    User = apps.get_model('base', 'User')
    for user in User.objects.all():
        user.email_verification_token = uuid.uuid4()
        user.is_email_verified = True  # existing users are already verified
        user.save(update_fields=['email_verification_token', 'is_email_verified'])


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0008_roomfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verification_token',
            field=models.UUIDField(default=uuid.uuid4, unique=False),
        ),
        migrations.AddField(
            model_name='user',
            name='is_email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(set_unique_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='email_verification_token',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]
