from django.urls import path
from . import views

urlpatterns = [
    path('login',views.loginpage,name='login'),
    path('logout',views.logoutpage,name='logout'),
    path('register',views.registerpage,name='register'),
    path('',views.home,name='home'),
    path('room/<str:pk>/',views.room,name='room'),
    path('profile/<str:pk>/',views.UserProfile,name='user-profile'),
    path('create-room/',views.CreateRoom,name='create-room'),
    path('update-room/<str:pk>/',views.UpdateRoom,name='update-room'),
    path('delete-room/<str:pk>/',views.DeleteRoom,name='delete-room'),
    path('delete-message/<str:pk>/',views.DeleteMessage,name='delete-message'),
    path('update-user/',views.UpdateUser,name='update-user'),
    path('topics/',views.topicspage,name='topics'),
    path('activity/',views.activitypage,name='activity'),
    path('online-status/',views.online_status,name='online-status'),
    path('notifications/',views.notifications_page,name='notifications'),
    path('notifications/count/',views.notifications_count,name='notifications-count'),
    path('inbox/',views.inbox,name='inbox'),
    path('dm/<str:user_id>/',views.dm_conversation,name='dm'),
    path('room/<str:pk>/upload/',views.upload_room_file,name='upload-room-file'),
    path('file/<str:pk>/delete/',views.delete_room_file,name='delete-room-file'),
]
