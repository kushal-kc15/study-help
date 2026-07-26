def notifications_count(request):
    if request.user.is_authenticated:
        from .models import DirectMessage
        notifs_qs = request.user.notifications.exclude(notification_type='message')
        unread_notifs = notifs_qs.filter(is_read=False).count()
        unread_dms = DirectMessage.objects.filter(recipient=request.user, is_read=False).count()
        recent_notifications = notifs_qs[:6]
        return {
            'unread_notifications': unread_notifs,
            'unread_dms': unread_dms,
            'recent_notifications': recent_notifications,
            'has_more_notifications': notifs_qs.count() > 6,
        }
    return {'unread_notifications': 0, 'unread_dms': 0, 'recent_notifications': [], 'has_more_notifications': False}
