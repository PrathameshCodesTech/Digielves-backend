from digielves_setup.models import Notification

from datetime import timedelta
from django.utils import timezone

def delete_old_seen_notifications():
    one_month_ago = timezone.now() - timedelta(days=60)

    old_seen_notifications = Notification.objects.filter(
        created_at__lt=one_month_ago,
        is_seen=True
    )

    # Delete these notifications
    old_seen_notifications.delete()

    return ""