from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Max, Count
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings as django_settings
from django.views.decorators.http import require_POST
from .access import is_room_member, is_room_muted
from .models import Room, Topic, Message, User, Notification, DirectMessage, RoomFile, MessageReaction
from .forms import RoomForm, UserForm, RegisterForm
from .sanitization import sanitize_markdown_source


# Create your views here.

def loginpage(request):
    page='login'
    if request.user.is_authenticated:
        return redirect('home')
    if request.method =='POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        user=authenticate(request,email=email,password=password)
        
        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            messages.error(request, 'invalid email or password')
    context={'page':page}
    return render(request, 'base/login_register.html',context)

@require_POST
def logoutpage(request):
    logout(request)
    return redirect('home')

ONBOARDING_TOPICS = [
    'Python', 'JavaScript', 'Web Development', 'Machine Learning', 'Data Science',
    'Algorithms', 'Mathematics', 'Physics', 'Chemistry', 'Biology',
    'Database', 'DevOps', 'Mobile Development', 'Cybersecurity', 'UI/UX Design',
    'Artificial Intelligence', 'Cloud Computing', 'Networking', 'Competitive Programming', 'Open Source',
]


def registerpage(request):
    form = RegisterForm()
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_email_verified = False
            user.save(update_fields=['is_email_verified'])
            _send_verification_email(request, user)
            login(request, user)
            return redirect('onboarding')
    return render(request, 'base/login_register.html', {'form': form})


@login_required(login_url='login')
def onboarding(request):
    if request.user.onboarding_complete and request.GET.get('redo') != '1':
        return redirect('home')

    if request.method == 'POST':
        interests_raw = request.POST.get('interests', '')
        selected = [t.strip() for t in interests_raw.split(',') if t.strip()]
        goal = request.POST.get('goal', '')
        level = request.POST.get('level', '')

        topics = []
        for name in selected:
            topic, _ = Topic.objects.get_or_create(name=name)
            topics.append(topic)

        user = request.user
        user.interests.set(topics)
        user.goal = goal
        user.level = level
        user.onboarding_complete = True
        user.save(update_fields=['goal', 'level', 'onboarding_complete'])

        return redirect('home')

    return render(request, 'base/onboarding.html', {
        'topics': ONBOARDING_TOPICS,
    })


@login_required(login_url='login')
@require_POST
def skip_onboarding(request):
    request.user.onboarding_complete = True
    request.user.save(update_fields=['onboarding_complete'])
    return redirect('home')


def onboarding_room_count(request):
    topics = [t.strip() for t in request.GET.get('topics', '').split(',') if t.strip()]
    count = Room.objects.filter(
        Q(tags__name__in=topics) | Q(topic__name__in=topics)
    ).distinct().count()
    return JsonResponse({'count': count})


def _send_verification_email(request, user):
    token = str(user.email_verification_token)
    verify_url = request.build_absolute_uri(f'/verify-email/{token}/')
    send_mail(
        subject='Verify your StudyHelp email',
        message=f'Hi {user.username},\n\nClick the link below to verify your email:\n{verify_url}\n\nThis link expires after first use.\n\nStudyHelp Team',
        from_email=getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'noreply@studyhelp.com'),
        recipient_list=[user.email],
        fail_silently=True,
    )


def verify_email(request, token):
    user = get_object_or_404(User, email_verification_token=token)
    if request.method != 'POST':
        return render(request, 'base/action_confirm.html', {
            'title': 'Verify your email',
            'prompt': f'Confirm verification for {user.email}.',
            'action_label': 'Verify email',
            'cancel_url': '/',
        })
    if not user.is_email_verified:
        user.is_email_verified = True
        user.save(update_fields=['is_email_verified'])
        messages.success(request, 'Email verified successfully!')
    else:
        messages.info(request, 'Email already verified.')
    return redirect('home')


@login_required(login_url='login')
@require_POST
def resend_verification(request):
    if request.user.is_email_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('home')
    _send_verification_email(request, request.user)
    messages.success(request, 'Verification email sent! Please check your inbox.')
    return redirect('home')

def home(request):
    from django.utils import timezone
    import datetime

    # Landing page for unauthenticated users
    if not request.user.is_authenticated:
        featured_rooms = Room.objects.select_related('host', 'topic').annotate(
            participant_count=Count('participants')
        ).order_by('-updated')[:6]
        landing_topics = Topic.objects.annotate(room_count=Count('room')).filter(room_count__gt=0).order_by('-room_count')[:8]
        context = {
            'total_rooms': Room.objects.count(),
            'total_users': User.objects.count(),
            'total_messages': Message.objects.count(),
            'featured_rooms': featured_rooms,
            'landing_topics': landing_topics,
        }
        return render(request, 'base/landing.html', context)

    q = request.GET.get('q', '')
    tab = request.GET.get('tab', 'for_you' if request.user.onboarding_complete else 'trending')

    if q:
        rooms_qs = Room.objects.filter(
            Q(topic__name__icontains=q) |
            Q(tags__name__icontains=q) |
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(host__username__icontains=q)
        ).distinct()
        tab = 'search'
    elif tab == 'joined':
        rooms_qs = Room.objects.filter(
            Q(participants=request.user) | Q(host=request.user)
        ).distinct()
    elif tab == 'for_you':
        user_interests = request.user.interests.all()
        if user_interests.exists():
            rooms_qs = Room.objects.filter(
                Q(tags__in=user_interests) | Q(topic__in=user_interests)
            ).distinct()
        else:
            rooms_qs = Room.objects.all()
    elif tab == 'trending':
        since = timezone.now() - datetime.timedelta(hours=24)
        rooms_qs = Room.objects.annotate(
            recent_messages=Count('message', filter=Q(message__created__gte=since))
        ).order_by('-recent_messages', '-updated')
    elif tab == 'new':
        rooms_qs = Room.objects.order_by('-created')
    elif tab == 'all':
        rooms_qs = Room.objects.all()
    else:
        rooms_qs = Room.objects.all()

    topics = Topic.objects.all()[0:5]
    room_count = rooms_qs.count()

    # Sidebar: 8 most recently active rooms with last message preview
    active_rooms = Room.objects.annotate(
        last_msg_time=Max('message__created')
    ).filter(last_msg_time__isnull=False).order_by('-last_msg_time').select_related('host', 'topic')[:8]

    paginator = Paginator(rooms_qs, 10)
    page_number = request.GET.get('page', 1)
    rooms = paginator.get_page(page_number)
    context = {
        'rooms': rooms,
        'topics': topics,
        'room_count': room_count,
        'active_rooms': active_rooms,
        'page_obj': rooms,
        'active_tab': tab,
        'q': q,
    }
    return render(request, 'base/home.html', context)

def room(request,pk):
    room=get_object_or_404(Room, id=pk)
    room_messages=room.message_set.all()
    participants=room.participants.all()
    is_participant = is_room_member(request.user, room)
    if request.method=='POST':
        if not is_participant:
            return redirect('room', pk=room.id)
        if is_room_muted(request.user, room):
            messages.error(request, 'You are muted in this room.')
            return redirect('room', pk=room.id)
        message=Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        other_participants = room.participants.exclude(id=request.user.id)
        Notification.objects.bulk_create([
            Notification(
                user=p,
                notification_type='message',
                message=f"@{request.user.username} sent a message in \"{room.name}\"",
                room=room,
                sender=request.user,
            ) for p in other_participants
        ])
        return redirect('room',pk=room.id)
    room_files = room.files.all()
    emojis = MessageReaction.EMOJIS
    is_muted = is_room_muted(request.user, room)
    context={
        'room': room,
        'room_messages': room_messages,
        'participants': participants,
        'room_files': room_files,
        'emojis': emojis,
        'is_muted': is_muted,
        'is_participant': is_participant,
    }
    return render(request, 'base/room.html',context)

def _process_tags(request, room):
    tag_names = [t.strip() for t in request.POST.get('tags', '').split(',') if t.strip()]
    tags = []
    for name in tag_names:
        tag, _ = Topic.objects.get_or_create(name=name.lower())
        tags.append(tag)
    room.tags.set(tags)
    if tags and not room.topic:
        room.topic = tags[0]
        room.save()


@login_required(login_url='login')
def CreateRoom(request):
    topics = Topic.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if not name:
            messages.error(request, 'Room name is required.')
        else:
            room = Room.objects.create(
                host=request.user,
                name=name,
                description=description,
            )
            _process_tags(request, room)
            return redirect('room', pk=room.id)
    context = {'topics': topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def UpdateRoom(request, pk):
    room = get_object_or_404(Room, id=pk)
    topics = Topic.objects.all()
    if request.user != room.host:
        return HttpResponse('You are not authorized to edit this room')
    if request.method == 'POST':
        room.name = request.POST.get('name', '').strip()
        room.description = request.POST.get('description', '').strip()
        room.save()
        _process_tags(request, room)
        return redirect('room', pk=room.id)
    existing_tags = ', '.join(room.tags.values_list('name', flat=True))
    context = {'topics': topics, 'room': room, 'existing_tags': existing_tags}
    return render(request, 'base/room_form.html', context)
@login_required(login_url='login')
def DeleteRoom(request,pk):
    room=get_object_or_404(Room, id=pk)
    if request.user!=room.host :
        return HttpResponse('You are not authorized to delete this room', status=403)
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html',{'obj':room})

@login_required(login_url='login')
def DeleteMessage(request,pk):
    message=get_object_or_404(Message, id=pk)
    if request.user!=message.user :
        return HttpResponse('You are not authorized to delete this message', status=403)
    
    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html',{'obj':message})

def UserProfile(request,pk):
    user=get_object_or_404(User, id=pk)
    rooms=user.room_set.all()
    room_messages=user.message_set.all()
    topics=Topic.objects.all()
    context={'user':user, 'rooms':rooms,'topics':topics,'room_messages':room_messages}
    return render(request, 'base/profile.html',context)
    
@login_required(login_url='login')
def UpdateUser(request):
    user = request.user
    form = UserForm(instance=user)
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
    return render(request, 'base/update-user.html', {'form': form})


@login_required(login_url='login')
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been deleted.')
        return redirect('home')
    return render(request, 'base/delete_account.html')

def topicspage(request):
    q=request.GET.get('q')if request.GET.get('q')!=None else ''
    topics=Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html',{'topics':topics})

def activitypage(request):
    room_messages=Message.objects.all()
    return render(request, 'base/activity.html',{'room_messages':room_messages})


@login_required(login_url='login')
def notifications_page(request):
    notifications = request.user.notifications.all()[:50]
    return render(request, 'base/notifications.html', {'notifications': notifications})


@login_required(login_url='login')
@require_POST
def mark_notifications_read(request):
    updated = request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({'marked_read': updated})


@login_required(login_url='login')
@require_POST
def upload_room_file(request, pk):
    room = get_object_or_404(Room, id=pk)
    if not is_room_member(request.user, room):
        return HttpResponse('You are not authorized to upload files to this room', status=403)
    if request.FILES.get('file'):
        f = request.FILES['file']
        RoomFile.objects.create(
            room=room,
            uploaded_by=request.user,
            file=f,
            original_name=f.name,
        )
    return redirect('room', pk=pk)


@login_required(login_url='login')
@require_POST
def delete_room_file(request, pk):
    room_file = get_object_or_404(RoomFile, id=pk)
    room_id = room_file.room.id
    if request.user != room_file.uploaded_by and request.user != room_file.room.host:
        return HttpResponse('You are not authorized to delete this file', status=403)
    room_file.file.delete(save=False)
    room_file.delete()
    return redirect('room', pk=room_id)


@login_required(login_url='login')
def notifications_count(request):
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})


def online_status(request):
    from .consumers import ONLINE_USERS
    return JsonResponse({'online_users': list(ONLINE_USERS)})


def user_badges(request, pk):
    user = get_object_or_404(User, id=pk)
    return JsonResponse({'badges': user.get_badges()})


def search_room_messages(request, pk):
    room = get_object_or_404(Room, id=pk)
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'results': [], 'count': 0})
    qs = room.message_set.filter(body__icontains=q).select_related('user')[:50]
    results = [{
        'id': m.id,
        'body': sanitize_markdown_source(m.body),
        'username': m.user.username,
        'avatar_url': m.user.avatar.url if m.user.avatar else '/media/avatar.svg',
        'user_id': m.user.id,
        'timesince': m.created.strftime('%b %d, %Y'),
    } for m in qs]
    return JsonResponse({'results': results, 'count': len(results)})


def room_messages_api(request, pk):
    room = get_object_or_404(Room, id=pk)
    before_id = request.GET.get('before')
    qs = room.message_set.all()
    if before_id:
        qs = qs.filter(id__lt=before_id)
    msgs = qs[:20]
    data = [{
        'id': m.id,
        'body': sanitize_markdown_source(m.body),
        'username': m.user.username,
        'avatar_url': m.user.avatar.url if m.user.avatar else '/media/avatar.svg',
        'user_id': m.user.id,
        'timestamp': m.created.isoformat(),
        'timesince': f"{m.created.strftime('%b %d')}",
    } for m in msgs]
    return JsonResponse({'messages': data, 'has_more': qs.count() > 20})


def room_reactions(request, pk):
    room = get_object_or_404(Room, id=pk)
    data = {}
    for message in room.message_set.all():
        counts = {}
        for e in MessageReaction.EMOJIS:
            c = message.reactions.filter(emoji=e).count()
            if c:
                counts[e] = c
        user_reactions = []
        if request.user.is_authenticated:
            user_reactions = list(message.reactions.filter(user=request.user).values_list('emoji', flat=True))
        if counts or user_reactions:
            data[str(message.id)] = {'counts': counts, 'user_reactions': user_reactions}
    return JsonResponse({'reactions': data})


@login_required(login_url='login')
@require_POST
def toggle_reaction(request, pk):
    message = get_object_or_404(Message, id=pk)
    if not is_room_member(request.user, message.room):
        return JsonResponse({'error': 'Not a participant'}, status=403)
    emoji = request.POST.get('emoji', '')
    if emoji not in MessageReaction.EMOJIS:
        return JsonResponse({'error': 'Invalid emoji'}, status=400)
    reaction, created = MessageReaction.objects.get_or_create(
        message=message, user=request.user, emoji=emoji
    )
    if not created:
        reaction.delete()
    counts = {}
    for e in MessageReaction.EMOJIS:
        c = message.reactions.filter(emoji=e).count()
        if c:
            counts[e] = c
    user_reactions = list(message.reactions.filter(user=request.user).values_list('emoji', flat=True))
    return JsonResponse({'counts': counts, 'user_reactions': user_reactions})


@login_required(login_url='login')
@require_POST
def join_room(request, pk):
    room = get_object_or_404(Room, id=pk)
    room.participants.add(request.user)
    return redirect('room', pk=room.id)


def join_via_invite(request, token):
    room = get_object_or_404(Room, invite_token=token)
    if not request.user.is_authenticated:
        messages.info(request, 'Please log in to join this room.')
        return redirect(f'/login?next=/invite/{token}/')
    if request.method != 'POST':
        return render(request, 'base/action_confirm.html', {
            'title': 'Join study room',
            'prompt': f'Join “{room.name}”?',
            'action_label': 'Join room',
            'cancel_url': f'/room/{room.id}/',
        })
    room.participants.add(request.user)
    return redirect('room', pk=room.id)


@login_required(login_url='login')
@require_POST
def regenerate_invite(request, pk):
    room = get_object_or_404(Room, id=pk)
    if request.user != room.host:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    import uuid
    room.invite_token = uuid.uuid4()
    room.save(update_fields=['invite_token'])
    invite_url = request.build_absolute_uri(f'/invite/{room.invite_token}/')
    return JsonResponse({'invite_url': invite_url})


@login_required(login_url='login')
@require_POST
def mute_user(request, room_pk, user_pk):
    room = get_object_or_404(Room, id=room_pk)
    if request.user != room.host:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    target = get_object_or_404(User, id=user_pk)
    if target == room.host or not room.participants.filter(id=target.id).exists():
        return JsonResponse({'error': 'User is not a mutable room participant'}, status=403)
    if room.muted_users.filter(id=user_pk).exists():
        room.muted_users.remove(target)
        muted = False
    else:
        room.muted_users.add(target)
        muted = True
    return JsonResponse({'muted': muted, 'user_id': user_pk})


@login_required(login_url='login')
@require_POST
def kick_user(request, room_pk, user_pk):
    room = get_object_or_404(Room, id=room_pk)
    if request.user != room.host:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    target = get_object_or_404(User, id=user_pk)
    if target == room.host or not room.participants.filter(id=target.id).exists():
        return JsonResponse({'error': 'User is not a removable room participant'}, status=403)
    room.participants.remove(target)
    room.muted_users.remove(target)
    return JsonResponse({'kicked': True, 'user_id': user_pk})


@login_required(login_url='login')
@require_POST
def pin_message(request, room_pk, msg_pk):
    room = get_object_or_404(Room, id=room_pk)
    if request.user != room.host:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    message = get_object_or_404(Message, id=msg_pk, room=room)
    if room.pinned_message_id == message.id:
        room.pinned_message = None
        pinned = False
    else:
        room.pinned_message = message
        pinned = True
    room.save(update_fields=['pinned_message'])
    return JsonResponse({
        'pinned': pinned,
        'msg_id': msg_pk,
        'body': sanitize_markdown_source(message.body[:100]),
    })


@login_required(login_url='login')
@require_POST
def toggle_bookmark(request, pk):
    room = get_object_or_404(Room, id=pk)
    if room.bookmarked_by.filter(id=request.user.id).exists():
        room.bookmarked_by.remove(request.user)
        bookmarked = False
    else:
        room.bookmarked_by.add(request.user)
        bookmarked = True
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'bookmarked': bookmarked})
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required(login_url='login')
def bookmarks(request):
    rooms = request.user.bookmarked_rooms.all()
    return render(request, 'base/bookmarks.html', {'rooms': rooms})


@login_required(login_url='login')
def inbox(request, user_id=None):
    me = request.user
    partner_ids = DirectMessage.objects.filter(
        Q(sender=me) | Q(recipient=me)
    ).values_list('sender', 'recipient')

    seen = set()
    for s, r in partner_ids:
        other = r if s == me.id else s
        seen.add(other)

    conversations = []
    for uid in seen:
        partner = User.objects.get(id=uid)
        last_msg = DirectMessage.objects.filter(
            Q(sender=me, recipient=partner) | Q(sender=partner, recipient=me)
        ).last()
        unread = DirectMessage.objects.filter(sender=partner, recipient=me, is_read=False).count()
        conversations.append({'partner': partner, 'last_msg': last_msg, 'unread': unread})

    conversations.sort(key=lambda x: x['last_msg'].created if x['last_msg'] else 0, reverse=True)

    context = {'conversations': conversations}

    if user_id:
        other = get_object_or_404(User, id=user_id)
        if me == other:
            return redirect('inbox')
        dm_messages = DirectMessage.objects.filter(
            Q(sender=me, recipient=other) | Q(sender=other, recipient=me)
        )
        context['active_chat'] = other
        context['dm_messages'] = dm_messages

    return render(request, 'base/inbox.html', context)


@login_required(login_url='login')
@require_POST
def mark_dm_read(request, user_id):
    other = get_object_or_404(User, id=user_id)
    updated = DirectMessage.objects.filter(
        sender=other,
        recipient=request.user,
        is_read=False,
    ).update(is_read=True)
    return JsonResponse({'marked_read': updated})


@login_required(login_url='login')
@require_POST
def send_room_message(request, pk):
    room = get_object_or_404(Room, id=pk)
    is_participant = is_room_member(request.user, room)
    if not is_participant:
        return JsonResponse({'error': 'Not a participant'}, status=403)
    if is_room_muted(request.user, room):
        return JsonResponse({'error': 'You are muted'}, status=403)
    body = request.POST.get('body', '').strip()
    if not body:
        return JsonResponse({'error': 'Empty message'}, status=400)
    message = Message.objects.create(user=request.user, room=room, body=body)
    other_participants = room.participants.exclude(id=request.user.id)
    Notification.objects.bulk_create([
        Notification(
            user=p,
            notification_type='message',
            message=f"@{request.user.username} sent a message in \"{room.name}\"",
            room=room,
            sender=request.user,
        ) for p in other_participants
    ])
    return JsonResponse({
        'id': message.id,
        'body': sanitize_markdown_source(message.body),
        'username': request.user.username,
        'avatar_url': request.user.avatar.url if request.user.avatar else '/static/images/avatar.svg',
        'user_id': request.user.id,
        'timestamp': 'just now',
    })


@login_required(login_url='login')
def poll_room_messages(request, pk):
    room = get_object_or_404(Room, id=pk)
    after_id = request.GET.get('after')
    if not after_id:
        return JsonResponse({'messages': []})
    msgs = room.message_set.filter(id__gt=after_id).select_related('user')
    data = [{
        'id': m.id,
        'body': sanitize_markdown_source(m.body),
        'username': m.user.username,
        'avatar_url': m.user.avatar.url if m.user.avatar else '/static/images/avatar.svg',
        'user_id': m.user.id,
        'timestamp': f"{m.created.strftime('%b %d, %H:%M')}",
    } for m in msgs]
    return JsonResponse({'messages': data})


@login_required(login_url='login')
@require_POST
def send_dm_message(request, user_id):
    other = get_object_or_404(User, id=user_id)
    body = request.POST.get('body', '').strip()
    if not body:
        return JsonResponse({'error': 'Empty message'}, status=400)
    dm = DirectMessage.objects.create(sender=request.user, recipient=other, body=body)
    Notification.objects.create(
        user=other,
        notification_type='message',
        message=f"@{request.user.username} sent you a direct message",
        sender=request.user,
    )
    return JsonResponse({
        'id': dm.id,
        'body': sanitize_markdown_source(dm.body),
        'sender_id': request.user.id,
        'username': request.user.username,
        'avatar_url': request.user.avatar.url if request.user.avatar else '/static/images/avatar.svg',
        'timestamp': 'just now',
    })


@login_required(login_url='login')
def poll_dm_messages(request, user_id):
    other = get_object_or_404(User, id=user_id)
    after_id = request.GET.get('after')
    if not after_id:
        return JsonResponse({'messages': []})
    me = request.user
    msgs = DirectMessage.objects.filter(
        Q(sender=me, recipient=other) | Q(sender=other, recipient=me),
        id__gt=after_id
    ).select_related('sender')
    data = [{
        'id': m.id,
        'body': sanitize_markdown_source(m.body),
        'sender_id': m.sender.id,
        'username': m.sender.username,
        'avatar_url': m.sender.avatar.url if m.sender.avatar else '/static/images/avatar.svg',
        'timestamp': f"{m.created.strftime('%H:%M')}",
    } for m in msgs]
    return JsonResponse({'messages': data})
