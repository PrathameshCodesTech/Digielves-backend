from datetime import datetime
from django.utils import timezone

from digielves_setup.models import Checklist, Notification, TaskHierarchy, TaskStatus, Tasks, User, notification_handler
from django.db.models import Q
from datetime import timedelta
from django.db.models import Count
from django.db.models.signals import post_save
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone as newTimezone

import logging

logger = logging.getLogger('api_hits')


def create_notification(user, task, msg_suffix):
    """
    Creates a new notification for the given task and user with a custom message suffix.

    Args:
        user (User): The user to whom the notification is created.
        task (Tasks): The task for which the notification is created.
        msg_suffix (str): The custom message suffix to be added to the notification message.
        
    Return:
        No Return
    """
    created_by = task.created_by
    assign_to_users = task.assign_to.all()

    notification_msg = f"Task '{task.task_topic}' {msg_suffix}"
    post_save.disconnect(notification_handler, sender=Notification)
    notification = Notification.objects.create(
        user_id=user,
        notification_msg=notification_msg,
        action_id=task.id,
        other_id=task.checklist.board.id if task.checklist else None,
        where_to="myboard" if task.checklist == None else "customboard",
        action_content_type=ContentType.objects.get_for_model(TaskHierarchy),
    )
    notification.notification_to.set(assign_to_users)
    notification.notification_to.add(created_by)
    post_save.connect(notification_handler, sender=Notification)
    post_save.send(sender=Notification, instance=notification, created=True)




def check_overdue_tasks():

    """
    Checks for overdue and about-to-end tasks, and creates notifications accordingly.
    """
    
    wip_fixed_status = {
        "Pending": "Pending",
        "InProgress": "InProgress",
        "OnHold" : "OnHold"
    }

    # Get the IDs of TaskStatus objects with fixed states from the wip_fixed_status dictionary
    not_fixed_state_ids = TaskStatus.objects.filter(
        fixed_state__in=wip_fixed_status.values(),
    ).values_list('id', flat=True)


    not_fixed_state_ids = list(not_fixed_state_ids)
    now = timezone.localtime(timezone.now())

    original_four_hour_later = now + newTimezone.timedelta(hours=4)


    overdue_tasks = TaskHierarchy.objects.filter(
        due_date__lte=now,
        status__in=not_fixed_state_ids,
        inTrash= False
    )

    about_to_end_tasks = TaskHierarchy.objects.filter(
        due_date__gte=now,
        due_date__lte=original_four_hour_later,
        status__in=not_fixed_state_ids,
        inTrash= False
    )


    user = User.objects.get(user_role="Dev::Admin")
    

    four_hours_ago = now - timedelta(hours=4)
    one_day_ago = now - timedelta(hours=23, minutes=58)
    
    existing_notifications_for_overdue = Notification.objects.filter(
        user_id=user,
        notification_msg__contains="due date passed",
        created_at__range=[one_day_ago, now],
    ).values_list('action_id', flat=True)
    
    existing_notifications_for_about_to_end = Notification.objects.filter(
        user_id=user,
        notification_msg__contains="approaching its due time",
        created_at__range=[four_hours_ago, now],
    ).values_list('action_id', flat=True)
    
    
    for task in overdue_tasks:
        if task.id not in existing_notifications_for_overdue:
            create_notification(user, task, "due date passed, Please update the Task Status")
    
    for task in about_to_end_tasks:
        if task.id not in existing_notifications_for_about_to_end:
            
            create_notification(user, task, "is approaching its due time. Please update the Task Status")
            
 