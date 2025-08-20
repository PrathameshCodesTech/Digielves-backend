from django.utils import timezone
from datetime import datetime, timedelta

from digielves_setup.models import EmployeePersonalDetails, Notification, OrganizationDetails, User, UserWorkSchedule, UserWorkSlot, notification_handler


from django.db.models.signals import post_save
from django.contrib.contenttypes.models import ContentType

def create_notification(user, work, other_id, slot):
    """
    Creates a new notification for the given task and user with a custom message suffix.

    Args:
        user (User): The user to whom the notification is created.
        task (Tasks): The task for which the notification is created.
        msg_suffix (str): The custom message suffix to be added to the notification message.
        
    Return:
        No Return
    """
    # org = EmployeePersonalDetails.objects.get(user_id = user).organization_id.id
    # org_1 = OrganizationDetails.objects.get(id = org).user_id.id
    # org_user = User.objects.get(id = org_1)
    employee_details = EmployeePersonalDetails.objects.select_related('organization_id__user_id').get(user_id=user)
    org_user = employee_details.organization_id.user_id



    notification_msg = f"You have pending work. Would you like to reschedule it for the next day?"
    post_save.disconnect(notification_handler, sender=Notification)
    notification = Notification.objects.create(
        user_id=org_user,
        notification_msg=notification_msg,
        action_id=work.id,
        other_id=other_id,
        where_to="userWorkSchedule",
        other_details = slot,
        action_content_type=ContentType.objects.get_for_model(UserWorkSchedule),
    )
    notification.notification_to.add(user)
    post_save.connect(notification_handler, sender=Notification)
    post_save.send(sender=Notification, instance=notification, created=True)



def get_users_with_ending_slots():
    try:
        # Get the current date and time
        current_date = timezone.now().date()
        current_time = timezone.now()

        # Calculate the time window for the next 15 minutes
        end_time_window = current_time + timedelta(minutes=45)

        # Get all work schedules for the current date
        work_schedules = UserWorkSchedule.objects.filter(date=current_date)
        
        ending_soon_user_info = {}

        for work_schedule in work_schedules:
            # Get all slots for the user's work schedule
            slots = UserWorkSlot.objects.filter(user_work_schedule=work_schedule).order_by('slot')

            if not slots:
                continue
            
            # Get the last slot of the day
            last_slot = slots.last()
            # Filter slots that end within the next 15 minutes
            if last_slot:
                slot_end_time_str = last_slot.slot.split(' - ')[1]  # Get the end time of the slot
                slot_end_time = datetime.strptime(slot_end_time_str, '%H:%M').time()
                slot_end_datetime = datetime.combine(current_date, slot_end_time)
                slot_end_datetime = timezone.make_aware(slot_end_datetime, timezone.get_default_timezone())

                if current_time <= slot_end_datetime <= end_time_window:
                    create_notification(work_schedule.user, work_schedule, last_slot.id, slot_end_time_str)
                    # Store user info with date, slot, and slot id
                    ending_soon_user_info[work_schedule.user.id] = {
                        'date': current_date,
                        'slot': last_slot.slot,
                        'slot_id': last_slot.id  # Include the UserWorkSlot id
                    }
                    # If a slot is found, break to avoid checking other slots for the same user
                    
        print("🐍 File: cron_task/find_ending_work_slots.py | Line: 49 | get_users_with_ending_slots ~ ending_soon_user_info",ending_soon_user_info)
        return ending_soon_user_info

    except Exception as e:
        print(f"Error in get_users_with_ending_slots: {e}")
        return {}

        


