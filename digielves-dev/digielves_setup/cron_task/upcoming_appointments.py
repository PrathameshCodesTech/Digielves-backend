from datetime import datetime, timedelta

from digielves_setup.models import DoctorConsultation, DoctorSlot, Notification, User, notification_handler
import logging

from django.db.models.signals import post_save

logger = logging.getLogger('api_hits')

def check_upcoming_appointments():
    logger.info(f"Cron API hit  Time: {datetime.now()}") 
    
    current_time = datetime.now().strftime("%H:%M")
    end_time = (datetime.now() + timedelta(minutes=10)).strftime("%H:%M")
    try:
        upcoming_slots = DoctorSlot.objects.filter(
            date=datetime.now().date(),
            freeze=True,
        ).distinct()
        user = User.objects.get(user_role="Dev::Admin")

        for slot in upcoming_slots:
            if current_time <= slot.slots.split(" - ")[0] <= end_time: 
                print(f"Slotss {slot.id} starts between {current_time} and {end_time}.")
                
                logger.info(f"Cron API hit  Time: {datetime.now()}") 
                
                try:
                    upcoming_appointments = DoctorConsultation.objects.get(
                                            doctor_slot=slot.id,
                                            status="Booked",
                                            confirmed="1"
                                        )
                    
                
                    
                    doctor = upcoming_appointments.doctor_id
                    employee = upcoming_appointments.employee_id
                    
                
                    existing_notification = Notification.objects.filter(
                                        user_id=user.id,
                                        action_id=upcoming_appointments.id
                                    ).last()
                    
                    
                    
                    if existing_notification == None:
                        
                    

                        notification_msg = (
                            f"Your consultation is about to start at {slot.slots.split(' - ')[0]}. "
                            f"Please be prepared and join the meeting on time."
                        )

                        post_save.disconnect(notification_handler, sender=Notification)
                        
                        notification = Notification.objects.create(
                                        user_id=user,
                                        notification_msg=notification_msg,
                                        action_id=upcoming_appointments.id
                                    )
                        # notification.notification_to.add(employee)
                        # notification.notification_to.add(doctor)
                        notification.notification_to.add(doctor, employee)

                        post_save.connect(notification_handler, sender=Notification)
                        post_save.send(sender=Notification, instance=notification, created=True)
                    else:
                        
                        pass
                
                except Exception as e:
                    logger.info(f"Cron API hit (Not so Imp) -  response: Error : {e} Time: {datetime.now()}") 
                    pass
                
            else:
                
                print(f"Slot {slot.id} does not start between {current_time} and {end_time}.")
                
    except Exception as e:
        logger.info(f"Cron API hit -  response: Error : {e} Time: {datetime.now()}") 
        
        pass

    

    # Create notifications for upcoming appointments
    # for appointment in upcoming_slots:
    #     doctor = appointment.doctor_id
    #     employee = appointment.employee_id

    #     # Check if a notification exists for the user and the time left is greater than 2 minutes
    #     existing_notification = Notification.objects.filter(
    #         user_id=doctor.id,
    #         notification_to=employee.id,
    #         action_id=appointment.id
    #     ).last()

    #     if not "upcoming appointment" in existing_notification.notification_msg or existing_notification.created_at + timedelta(minutes=2) < datetime.now():
    #         notification_msg = f"Upcoming appointment for {appointment.appointment_date} with {employee.firstname} {employee.lastname}."
    #         print(notification_msg)

    #         doctor_user = User.objects.get(id=doctor.id)
    #         employee_user = User.objects.get(id=employee.id)

    #         notification = Notification.objects.create(
    #             user_id=doctor_user,
    #             notification_msg=notification_msg,
    #             action_id=appointment.id
    #         )
    #         notification.notification_to.add(employee_user)
