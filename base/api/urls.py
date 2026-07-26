from django.urls import path
from . import views
from base.views import onboarding_room_count

urlpatterns = [
    path('',views.getRoutes),
    path('rooms/',views.getrooms),
    path('rooms/<str:pk>/',views.getroom),
    path('room-count/',onboarding_room_count),
]
