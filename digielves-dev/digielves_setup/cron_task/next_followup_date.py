from datetime import datetime, timedelta

from digielves_setup.models import Meettings, Notification, SalesLead, User, notification_handler
import logging

from django.db.models.signals import post_save
from django.utils import timezone

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone as django_timezone
import pytz


logger = logging.getLogger('api_hits')

def check_next_followup_date():
    current_datetime = django_timezone.now()
    now = timezone.localtime(timezone.now())
    ist = pytz.timezone('Asia/Kolkata')

    tomorrow_date = current_datetime + timedelta(days=1)
    
    upcoming_followup_tomorrow = SalesLead.objects.filter(
        next_followup_date__date=tomorrow_date.date(),
        next_followup_date__gt=current_datetime,
    ).distinct()
    
    
    
    one_hour_later = current_datetime + timedelta(hours=1)
    
    upcoming_followup_one_hour = SalesLead.objects.filter(
        next_followup_date__lte=one_hour_later,
        next_followup_date__gt=current_datetime,
    ).distinct()
    
    
    one_day_ago = now - timedelta(days=1)
    user = User.objects.get(user_role="Dev::Admin")
    
    
    
    
    for sale_lead in upcoming_followup_tomorrow:
        existing_notification = Notification.objects.filter(
            user_id=user.id,
            notification_msg__contains="next follow-up is tomorrow",
            action_id=sale_lead.id,
            created_at__range=[one_day_ago, now],
        ).last()

        if existing_notification is None:
            next_followup_date_ist = sale_lead.next_followup_date.astimezone(ist)
            notification_msg = f"just a quick reminder that your next follow-up is tomorrow on {next_followup_date_ist.strftime('%A, %B %d, %Y at %I:%M %p %Z')}. Let's make it a successful one!"

            post_save.disconnect(notification_handler, sender=Notification)
            
            notification = Notification.objects.create(
                user_id=user,
                notification_msg=notification_msg,
                where_to="sales",
                action_id=sale_lead.id,
                action_content_type=ContentType.objects.get_for_model(SalesLead),
            )
            users_to_notify = list(sale_lead.assign_to.all())
            notification.notification_to.set(users_to_notify)

            post_save.connect(notification_handler, sender=Notification)
            post_save.send(sender=Notification, instance=notification, created=True)
    
    # Send notification for follow-ups due in one hour
    fifteen_minute_ago = now - timedelta(minutes=15)
    for sale_lead in upcoming_followup_one_hour:
        existing_notification = Notification.objects.filter(
            user_id=user.id,
            notification_msg__contains="next follow-up is in one hour",
            action_id=sale_lead.id,
            created_at__range=[fifteen_minute_ago, now],
        ).last()

        if existing_notification is None:
            notification_msg = f"just a quick reminder that your next follow-up is in one hour. Let's make it a successful one!"

            post_save.disconnect(notification_handler, sender=Notification)
            
            notification = Notification.objects.create(
                user_id=user,
                notification_msg=notification_msg,
                where_to="sales",
                action_id=sale_lead.id,
                action_content_type=ContentType.objects.get_for_model(SalesLead),
            )
            users_to_notify = list(sale_lead.assign_to.all())
            notification.notification_to.set(users_to_notify)

            post_save.connect(notification_handler, sender=Notification)
            post_save.send(sender=Notification, instance=notification, created=True)

    
    
