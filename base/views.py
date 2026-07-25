from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Max, OuterRef, Subquery
from .models import Room, Topic, Message, User, Notification, DirectMessage, RoomFile
from .forms import RoomForm, UserForm, myusercreationform
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


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

from django.views.decorators.http import require_POST

@require_POST
def logoutpage(request):
    logout(request)
    return redirect('home')

def registerpage(request):
    form=myusercreationform()
    if request.method =='POST':
        form=myusercreationform(request.POST)
        if form.is_valid():
            user=form.save(commit=False)
            user.username=user.username.lower()
            user.save()
            login(request,user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration')
    return render(request,'base/login_register.html',{'form':form})

def home(request):
    q = request.GET.get('q', '')
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(tags__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q) |
        Q(host__username__icontains=q)
    ).distinct()
    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(
        Q(room__topic__name__icontains=q) |
        Q(room__name__icontains=q)
    )
    context = {'rooms': rooms, 'topics': topics, 'room_count': room_count, 'room_messages': room_messages}
    return render(request, 'base/home.html',context)

def room(request,pk):
    room=get_object_or_404(Room, id=pk)
    room_messages=room.message_set.all()
    participants=room.participants.all()
    if request.method=='POST':
        message=Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
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
    context={'room':room,'room_messages':room_messages,'participants':participants,'room_files':room_files}
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
        return HttpResponse('You are not authorized to delete this room')
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html',{'obj':room})

@login_required(login_url='login')
def DeleteMessage(request,pk):
    message=get_object_or_404(Message, id=pk)
    if request.user!=message.user :
        return HttpResponse('You are not authorized to delete this room')
    
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
    user=request.user
    form=UserForm(instance=user)
    if request.method == 'POST':
        form=UserForm(request.POST,request.FILES,instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile',pk=user.id)
    return render(request, 'base/update-user.html',{'form':form})

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
    unread = request.user.notifications.filter(is_read=False)
    unread.update(is_read=True)
    return render(request, 'base/notifications.html', {'notifications': notifications})


@login_required(login_url='login')
def upload_room_file(request, pk):
    room = get_object_or_404(Room, id=pk)
    if request.method == 'POST' and request.FILES.get('file'):
        f = request.FILES['file']
        RoomFile.objects.create(
            room=room,
            uploaded_by=request.user,
            file=f,
            original_name=f.name,
        )
    return redirect('room', pk=pk)


@login_required(login_url='login')
def delete_room_file(request, pk):
    room_file = get_object_or_404(RoomFile, id=pk)
    room_id = room_file.room.id
    if request.user == room_file.uploaded_by or request.user == room_file.room.host:
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


@login_required(login_url='login')
def inbox(request):
    me = request.user
    # Find all users this person has exchanged DMs with
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
    return render(request, 'base/inbox.html', {'conversations': conversations})


@login_required(login_url='login')
def dm_conversation(request, user_id):
    me = request.user
    other = get_object_or_404(User, id=user_id)
    if me == other:
        return redirect('inbox')

    messages_qs = DirectMessage.objects.filter(
        Q(sender=me, recipient=other) | Q(sender=other, recipient=me)
    )
    # mark received messages as read
    messages_qs.filter(recipient=me, is_read=False).update(is_read=True)

    return render(request, 'base/dm_conversation.html', {
        'other': other,
        'messages': messages_qs,
    })