from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from social_django.views import auth as _social_auth_view


urlpatterns = [
    path('admin/', admin.site.urls),

    # App URLs
    path('', include('base.urls')),
    path('api/', include('base.api.urls')),

    # Google OAuth
    path(
        'social-auth/login/google-oauth2/',
        _social_auth_view,
        {'backend': 'google-oauth2'},
        name='google-oauth2-begin',
    ),

    # social-auth URLs
    path(
        'social-auth/',
        include('social_django.urls', namespace='social')
    ),

    # Password reset
    path(
        'auth/password_reset/',
        auth_views.PasswordResetView.as_view(),
        name='password_reset'
    ),
    path(
        'auth/password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(),
        name='password_reset_done'
    ),
    path(
        'auth/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
    path(
        'auth/reset/done/',
        auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete'
    ),
]


urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)
