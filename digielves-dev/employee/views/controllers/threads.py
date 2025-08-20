

from digielves_setup.models import Notification, SubTaskChild, SubTasks, User, notification_handler
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save

def send_notification_for_chat(sender, task, from_where):
    try:
        subtask_users = SubTasks.objects.filter(Task=task).values_list('assign_to', 'created_by')
        subtask_child_users = SubTaskChild.objects.filter(subtasks__Task=task).values_list('assign_to', 'created_by')

        # Collect all unique users
        user_ids = set()
        user_ids.update(task.assign_to.values_list('id', flat=True))
        user_ids.add(task.created_by.id)

        for subtask in subtask_users:

            user_ids.update(subtask)

        for subtask_child in subtask_child_users:
            user_ids.update(subtask_child)

        # Exclude the sender from the notification list
        user_ids.discard(sender.id)

        notification_msg = f"{sender.firstname} sent a new chat in task '{task.task_topic}'."
        post_save.disconnect(notification_handler, sender=Notification)

        notification = Notification.objects.create(
            user_id=sender,
            notification_msg=notification_msg,
            action_content_type=ContentType.objects.get_for_model(task),
            action_id=task.id,
            where_to="customboard" if task.checklist else "myboard"
        )
        print(user_ids)
        notification.notification_to.set(User.objects.filter(id__in=user_ids))

        post_save.connect(notification_handler, sender=Notification)
        post_save.send(sender=Notification, instance=notification, created=True)

    except Exception as e:
        print("Error in send_notification_for_chat:", str(e))
        


           