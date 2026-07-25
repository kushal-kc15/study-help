from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Room, Topic, Message, User
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
    q=request.GET.get('q')if request.GET.get('q')!=None else ''
    rooms = Room.objects.filter(
        Q(topic__name__contains=q) 
        # Q(name__icontains=q) |
        # Q(description__icontains=q) 
        )
    topics=Topic.objects.all()[0:5]
    room_count=rooms.count()
    room_messages=Message.objects.filter(
        Q(room__topic__name__icontains=q)
    )
    context={'rooms':rooms,'topics':topics,'room_count':room_count,'room_messages':room_messages}
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
        return redirect('room',pk=room.id)
    context={'room':room,'room_messages':room_messages,'participants':participants}
    return render(request, 'base/room.html',context)

@login_required(login_url='login')
def CreateRoom(request):
    form=RoomForm()
    topics=Topic.objects.all()
    if request.method == 'POST':
        topic_name=request.POST.get('topic')
        topic,created=Topic.objects.get_or_create(name=topic_name)
        
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description') 
        )
        return redirect('home')
    context={'form':form,'topics':topics}
    return render(request, 'base/room_form.html',context)
@login_required(login_url='login')
def UpdateRoom(request,pk):
    room=get_object_or_404(Room, id=pk)
    topics=Topic.objects.all()
    form=RoomForm(instance=room)
    if request.user!=room.host :
        return HttpResponse('You are not authorized to edit this room')
    if request.method == 'POST':
        topic_name=request.POST.get('topic')
        topic,created=Topic.objects.get_or_create(name=topic_name)
        room.name=request.POST.get('name')
        room.description=request.POST.get('description')
        room.topic=topic
        room.save()
        return redirect('home')
    context={'form':form,'topics':topics,'room':room}
    return render(request, 'base/room_form.html',context)
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