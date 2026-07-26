import re
from .models import User


def _generate_username(email):
    base = re.sub(r'[^a-z0-9]', '', email.split('@')[0].lower()) or 'user'
    username = base
    n = 1
    while User.objects.filter(username=username).exists():
        username = f'{base}{n}'
        n += 1
    return username


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}

    email = details.get('email', '').lower()
    if not email:
        return

    # Reuse existing account with same email
    try:
        existing = User.objects.get(email=email)
        return {'is_new': False, 'user': existing}
    except User.DoesNotExist:
        pass

    username = _generate_username(email)
    name = details.get('fullname') or f"{details.get('first_name','')} {details.get('last_name','')}".strip()

    user = User.objects.create_user(
        username=username,
        email=email,
        password=None,          # no password — Google auth only
        name=name or None,
        is_email_verified=True, # Google already verified the email
    )
    return {'is_new': True, 'user': user}


def update_profile(strategy, details, user=None, is_new=False, *args, **kwargs):
    if not user:
        return

    changed = []

    if not user.name:
        name = details.get('fullname') or f"{details.get('first_name','')} {details.get('last_name','')}".strip()
        if name:
            user.name = name
            changed.append('name')

    if not user.is_email_verified:
        user.is_email_verified = True
        changed.append('is_email_verified')

    if changed:
        user.save(update_fields=changed)

    # Send new Google users through onboarding
    if is_new:
        return {'next': '/onboarding/'}
