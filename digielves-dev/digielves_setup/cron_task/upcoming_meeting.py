from datetime import datetime, timedelta

from digielves_setup.models import Meettings, Notification, User, notification_handler
import logging

from django.db.models.signals import post_save
from django.utils import timezone

from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger('api_hits')

def check_upcoming_meeting():
    now = timezone.localtime(timezone.now())
    
    original_datetime = now.strftime('%Y-%m-%d')
    current_time = datetime.now().strftime("%H:%M")
    end_time = (datetime.now() + timedelta(minutes=15)).strftime("%H:%M")

    try:
        upcoming_meetings = Meettings.objects.filter(
            from_date=original_datetime,
            from_time__gte = current_time,
            from_time__lte = end_time, 
            status_complete=False
        ).distinct()
        print(upcoming_meetings)
        
        fifteen_min_ago = now - timedelta(minutes=15)
        
        for meeting in upcoming_meetings:
            
            user = User.objects.get(user_role="Dev::Admin")
            existing_notification = Notification.objects.filter(
                        user_id=user.id,
                        notification_msg__contains = "Your meeting with title",
                        action_id=meeting.id,
                        created_at__range=[fifteen_min_ago, now],
                    ).last()
                        
            if existing_notification == None:
                notification_msg = f"Your meeting with title '{meeting.title}' is about to start at {meeting.from_time.strftime('%H:%M')}. Please get ready."

                post_save.disconnect(notification_handler, sender=Notification)
                
                notification = Notification.objects.create(
                                user_id=user,
                                notification_msg=notification_msg,
                                where_to = "meeting",
                                action_id=meeting.id,
                                action_content_type=ContentType.objects.get_for_model(Meettings),
                            )
                users_to_notify = list(meeting.participant.all())
                users_to_notify.append(meeting.user_id)
                notification.notification_to.set(users_to_notify)
                

                post_save.connect(notification_handler, sender=Notification)
                post_save.send(sender=Notification, instance=notification, created=True)
            else:
                
                pass
    
        
                
    except Exception as e:
        logger.info(f"Cron API hit -  response: Error : {e} Time: {datetime.now()}") 
        
        pass