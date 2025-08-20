from django.http import JsonResponse

from digielves_setup.helpers.error_trace import create_error_response
from digielves_setup.models import CalenderReminder, DoctorConsultation, Events, MeettingSummery, Meettings, ReminderToSchedule, TaskHierarchy, Tasks, User, UserWorkSchedule, UserWorkSlot
from employee.seriallizers.calender.calender_seriallizaers import CombinedEventMeetingSerializer, EventCalenderSerializer, GetSpecificDoctorConsultationSerializer, GetSpecificEventsSerializer, GetSpecificMeetingCalenderSerializer, GetSpecificTaskHierarchySerializer, GetSpecificTaskSerializer, MeetingCalenderSerializer, MeetingSummarySerializer, TaskForRescheduleSerializer, TaskHierarchyCalenderSerializer, TaskHierarchyForRescheduleSerializer, TasksCalenderSerializer
from employee.views.controllers.status_controllers import get_status_ids_from_assigned_side
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.utils.dateparse import parse_datetime
from datetime import datetime, timedelta
class CalenderViewSet(viewsets.ModelViewSet):
    
    @csrf_exempt
    def get_available_slots(self, request):
        try:
            user_id = request.GET.get('user_id')
            
            if not user_id:
                return JsonResponse({'success': False, 'status': 'Missing user_id parameter'}, status=400)

            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'status': 'User not found'}, status=404)

            current_date = timezone.now().date() + timedelta(days=1)  # Start checking from the next day
            days_to_check = 7  # Number of days to look ahead

            for day_offset in range(days_to_check):
                date_to_check = current_date + timedelta(days=day_offset)
                work_schedules = UserWorkSchedule.objects.filter(user=user, date=date_to_check)
                
                if work_schedules.exists():
                    for schedule in work_schedules:
                        available_slot = UserWorkSlot.objects.filter(
                            user_work_schedule=schedule,
                            freeze=False
                        ).order_by('slot').first()
                        
                        if available_slot:
                            # Check if the slot overlaps with any CalenderReminder
                            slot_start_time = datetime.strptime(available_slot.slot.split(' - ')[0], '%H:%M').time()
                            slot_end_time = datetime.strptime(available_slot.slot.split(' - ')[1], '%H:%M').time()
                            slot_start_datetime = datetime.combine(schedule.date, slot_start_time)
                            slot_end_datetime = datetime.combine(schedule.date, slot_end_time)
                            slot_start_datetime = timezone.make_aware(datetime.combine(schedule.date, slot_start_time))
                            slot_end_datetime = timezone.make_aware(datetime.combine(schedule.date, slot_end_time))

                        
                            
                            
                            overlapping_reminders = CalenderReminder.objects.filter(
                            user=user,
                            category__in=['Task', 'Meeting'],
                            from_datetime__gte=slot_start_datetime,
                            from_datetime__lt=slot_end_datetime
                        )
                            print(overlapping_reminders)
                        
                            
                            if not overlapping_reminders.exists():
                                nearest_slot_datetime = slot_start_datetime
                                nearest_slot_full = nearest_slot_datetime.strftime('%Y-%m-%d %H:%M')
                                return JsonResponse({
                                    'success': True,
                                    'nearest_slot': {
                                        'id': available_slot.id,
                                        'full_date': nearest_slot_full
                                    }
                                }, status=200)

            return JsonResponse({'success': True, 'status': 'No slots available', 'message': f'No available slots found in the next {days_to_check} days'}, status=200)
        
        except Exception as e:
            return JsonResponse({'success': False, 'status': 'Error', 'message': str(e)}, status=500)

        
    @csrf_exempt
    def get_due_task(self, request):
        user_id = request.GET.get('user_id')
            
        if not user_id:
            return JsonResponse({'success': False, 'status': 'Missing user_id parameter'}, status=400)
        
        try:
            current_time = datetime.now()
            opened_status_ids = get_status_ids_from_assigned_side(user_id)
            
            
            task_content_type = ContentType.objects.get_for_model(Tasks)
            # Get the IDs of tasks that have future scheduled times in ReminderToSchedule
            future_scheduled_task_ids = ReminderToSchedule.objects.filter(
                user_id=user_id,
                content_type=task_content_type,
                scheduled_time__gt=current_time
            ).values_list('object_id', flat=True)
        
        
        
            tasks = Tasks.objects.filter(
                Q(status__id__in=opened_status_ids),
                ~Q(id__in=future_scheduled_task_ids), 
                Q(due_date__lte=current_time),
                Q(created_by_id=user_id) | Q(assign_to__id=user_id),
                is_personal=False,
                inTrash=False
            ).distinct().order_by('due_date')

            user_serializer = TaskForRescheduleSerializer(tasks, many=True)
            return JsonResponse({'success': True, 'status': 200, 'data': user_serializer.data}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return JsonResponse({'success': False, 'status': 'Error retrieving tasks', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    
    @csrf_exempt
    def reschedule_event(self, request):

        
        user_id = request.POST.get('user_id')
        category = request.POST.get('category')
        object_id = request.POST.get('object_id')
        slot_id = request.POST.get('slot_id')

        if not all([user_id, category, object_id, slot_id]):
            return JsonResponse({'success': False, 'message': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            slot = UserWorkSlot.objects.get(id=slot_id)
            date = slot.user_work_schedule.date.strftime('%Y-%m-%d')
            start_time = slot.slot.split(' - ')[0]  # Extract the start time
            scheduled_time_str = f"{date} {start_time}"
            scheduled_time = parse_datetime(scheduled_time_str)

            if scheduled_time is None:
                raise ValueError("Invalid datetime format")

        except UserWorkSlot.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Slot not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if category == 'task':
                content_type = ContentType.objects.get_for_model(Tasks)
            elif category == 'meeting':
                content_type = ContentType.objects.get_for_model(Meettings)
            else:
                return JsonResponse({'success': False, 'message': 'Invalid category'}, status=status.HTTP_400_BAD_REQUEST)

            reminder = ReminderToSchedule.objects.create(
                user_id=user_id,
                content_type=content_type,
                object_id=object_id,
                scheduled_time=scheduled_time,
                calendar_reminder=None  # Handle calendar reminder if needed
            )

            slot.freeze = True
            slot.save()

        except Exception as e:
            return JsonResponse({'success': False, 'message': f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return JsonResponse({'success': True, 'message': 'Reminder scheduled successfully'}, status=status.HTTP_201_CREATED)

    @csrf_exempt
    def get_category_wise_calender_reminder(self, request):
        try:
            user_id = request.GET.get('user_id')
            category = request.GET.get('category')
            object_id = request.GET.get('object_id')
            summery = request.GET.get('summery')
            print(category, object_id)
        
            if user_id:
                if category and object_id:
                    if category=='Event':
                        obj = Events.objects.filter(id=object_id)
                        serializer = GetSpecificEventsSerializer(obj, many=True)
                    
                    elif category=='Task':
                        obj = Tasks.objects.filter(id=object_id)
                        serializer = GetSpecificTaskSerializer(obj, many=True)
                    
                    elif category=='Meeting':
                        obj = Meettings.objects.filter(id=object_id).first()
                        if summery == 'true' or summery == True or summery == "True":  # Check if summery is true
                            meeting_data = GetSpecificMeetingCalenderSerializer(obj).data
                            meeting_summary = MeettingSummery.objects.filter(meettings=obj).first()
                            if meeting_summary:
                                summary_data = MeetingSummarySerializer(meeting_summary).data
                                return JsonResponse({
                                    "success": True,
                                    "status": status.HTTP_200_OK,
                                    "message": "Calendar Reminder with Meeting Summary retrieved successfully",
                                    "data": meeting_data,
                                    "summery":summary_data 
                                })
                            else:
                                return JsonResponse({
                                    "success": True,
                                    "status": status.HTTP_200_OK,
                                    "message": "retrieved successfully",
                                    "data": meeting_data
                                })
                        else:
                            serializer = GetSpecificMeetingCalenderSerializer(obj)
                        
                    elif category== 'Consultation':
                        obj = DoctorConsultation.objects.filter(id=object_id)
                        serializer = GetSpecificDoctorConsultationSerializer(obj, many=True)
                    
                    return JsonResponse({
                        "success": True,
                        "status": status.HTTP_200_OK,                
                        "message": "Calender Reminder retrieved successfully",
                        "data":  serializer.data
                    })
                else:
                    return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,                
                    "message": "Missing 'user_id' parameter"
                })
            else:
                return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,                
                "message": "Missing 'user_id' parameter"
            })
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @csrf_exempt
    def updateEventMeetingTask(self, request):
        try:
            user_id = request.data.get('user_id')
            category = request.data.get('category')
            obj_id = request.data.get('id')
            print(user_id, category, obj_id)

            if not user_id or not category or not obj_id:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Invalid request. user_id, category, and id are required."
                })

            user = User.objects.get(id=user_id)

            if category == 'Event':
                try:
                    event = Events.objects.get(id=obj_id, user_id=user)
                    eventSerialData = EventCalenderSerializer(event, data=request.data)
                    if eventSerialData.is_valid(raise_exception=True):
                        save_event = eventSerialData.save()

                        guest_ids = request.data.get('guest_ids', ',')
                        guest_user_ids = [int(id) for id in guest_ids.split(',') if id]
                        guest_users = User.objects.filter(id__in=guest_user_ids)
                        event.guest.set(guest_users)
                        event.save()
                        

                        return JsonResponse({
                            "success": True,
                            "status": status.HTTP_200_OK,
                            "message": "Event updated successfully",
                            "data": EventCalenderSerializer(save_event).data
                        })
                except Events.DoesNotExist:
                    pass

            elif category == 'Meeting':
                try:
                    meeting = Meettings.objects.get(id=obj_id, user_id=user)
                    meetingSerialData = MeetingCalenderSerializer(meeting, data=request.data)
                    if meetingSerialData.is_valid(raise_exception=True):
                        save_meeting = meetingSerialData.save()

                        participent_ids = request.data.get('participent_ids', ',')
                        participent_user_ids = [int(id) for id in participent_ids.split(',') if id]
                        participent_users = User.objects.filter(id__in=participent_user_ids)

                        
                        meeting.participant.set(participent_users)
                        meeting.save()

                        return JsonResponse({
                            "success": True,
                            "status": status.HTTP_200_OK,
                            "message": "Meeting updated successfully",
                            "data": MeetingCalenderSerializer(save_meeting).data
                        })
                except Meettings.DoesNotExist:
                    pass


            elif category == 'Task':
                try:
                    task = Tasks.objects.get(id=obj_id, created_by=user)
                    taskSerialData = TasksCalenderSerializer(task, data=request.data)
                    if taskSerialData.is_valid(raise_exception=True):
                        assigned = request.data.get('assign_to', ',')
                        assign_user_ids = [int(id) for id in assigned.split(',') if id]
                        assign_users = User.objects.filter(id__in=assign_user_ids)
                        task.assign_to.clear()
                        task.assign_to.set(assign_users)
                        save_task = taskSerialData.save()
                        

                        return JsonResponse({
                            "success": True,
                            "status": status.HTTP_200_OK,
                            "message": "Task updated successfully",
                            "data": TasksCalenderSerializer(save_task).data
                        })
                except Tasks.DoesNotExist:
                    pass

            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": f"No {category} found with the given ID for the user."
            })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found"
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update object",
                "errors": str(e)
            })
    #  working but not calender reminder logic
    # @csrf_exempt
    # def get_available_slots(self, request):
    #     try:
    #         user_id = request.GET.get('user_id')
            
    #         if not user_id:
    #             return JsonResponse({'success': False, 'status': 'Missing user_id parameter'}, status=400)

    #         try:
    #             user = User.objects.get(pk=user_id)
    #         except User.DoesNotExist:
    #             return JsonResponse({'success': False, 'status': 'User not found'}, status=404)

    #         current_date = timezone.now().date() + timedelta(days=1)  # Start checking from the next day
    #         days_to_check = 7  # Number of days to look ahead

    #         for day_offset in range(days_to_check):
    #             date_to_check = current_date + timedelta(days=day_offset)
    #             work_schedules = UserWorkSchedule.objects.filter(user=user, date=date_to_check)
                
    #             if work_schedules.exists():
    #                 for schedule in work_schedules:
    #                     available_slot = UserWorkSlot.objects.filter(
    #                         user_work_schedule=schedule,
    #                         freeze=False
    #                     ).order_by('slot').first()
                        
    #                     if available_slot:
    #                         nearest_slot_datetime = datetime.combine(schedule.date, datetime.strptime(available_slot.slot.split(' - ')[0], '%H:%M').time())
    #                         nearest_slot_full = nearest_slot_datetime.strftime('%Y-%m-%d %H:%M')
    #                         return JsonResponse({
    #                             'success': True,
    #                             'nearest_slot': {
    #                                 'id': available_slot.id,
    #                                 'full_date': nearest_slot_full
    #                             }
    #                         }, status=200)

    #         return JsonResponse({'success': True, 'status': 'No slots available', 'message': f'No available slots found in the next {days_to_check} days'}, status=200)
        
    #     except Exception as e:
    #         return JsonResponse({'success': False, 'status': 'Error', 'message': str(e)}, status=500)
    
    

    @csrf_exempt
    def get_all_events(self, request):
        
        try:
            user_id = request.GET.get('user_id')
            month = request.GET.get('month')
            year = request.GET.get('year')

            if user_id is None:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Invalid request. user_id is required."
                })

            user = User.objects.get(id=user_id)

            
            if month:
                
                guest_events = Events.objects.filter(
                    (Q(user_id=user) | Q(guest=user)) & Q(from_date__month=month)
                ).distinct()

                
                participant_meetings = Meettings.objects.filter(
                    (Q(user_id=user) | Q(participant=user)) & Q(from_date__month=month)
                ).distinct()

                
                # print(participant_meetings)

                
                user_tasks = TaskHierarchy.objects.filter(
                (Q(created_by=user) | Q(assign_to=user)) & Q(due_date__year=year) & Q(due_date__month=month), inTrash = False
                ).distinct()



            else:
                
                guest_events = Events.objects.filter(Q(user_id=user) | Q(guest=user)).distinct().order_by('-created_at')
                participant_meetings = Meettings.objects.filter(Q(user_id=user) | Q(participant=user)).distinct().order_by('-created_at')
                user_tasks = TaskHierarchy.objects.filter(Q(created_by=user) | Q(assign_to=user), inTrash = False).distinct()
                
                
                user_consultation = DoctorConsultation.objects.filter(
                    Q(employee_id=user) & ~Q(status="Cancelled") 
                ).distinct()
                current_time = timezone.now()
                
                rescheduled_data = ReminderToSchedule.objects.filter(
                    Q(user=user) & Q(scheduled_time__gte=current_time)
                ).distinct()
             


            # events_and_meetings = list(rescheduled_data)
            events_and_meetings = list(guest_events) + list(participant_meetings) + list(user_tasks)  + list(user_consultation) + list(rescheduled_data)


            
            combined_serializer = CombinedEventMeetingSerializer(events_and_meetings, many=True)
            
              
            data_with_users = []

            for item in combined_serializer.data:
                if 'guest_ids' in item:
                    guest_ids = item['guest_ids']
                    guests = User.objects.filter(id__in=guest_ids).values('id', 'firstname', 'lastname', 'email')
                    item['guest_data'] = list(guests)

                if 'participant_ids' in item:
                    participant_ids = item['participant_ids']
                    participants = User.objects.filter(id__in=participant_ids).values('id', 'firstname', 'lastname', 'email')
                    item['participant_data'] = list(participants)

                if 'assign_to_ids' in item:
                    assign_to_ids = item['assign_to_ids']
                    assignees = User.objects.filter(id__in=assign_to_ids).values('id', 'firstname', 'lastname', 'email')
                    item['assign_to_data'] = list(assignees)

                data_with_users.append(item)

            response = {
                "success": True,
                "status": 200,
                "message": "Events and meetings retrieved successfully",
                "data": data_with_users
            }

            return JsonResponse(response)

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": "User not found"
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": "Failed to retrieve events and meetings",
                "errors": str(e)
            })
            
    
    @csrf_exempt
    def get_dued_task(self, request):
        user_id = request.GET.get('user_id')
            
        if not user_id:
            return JsonResponse({'success': False, 'status': 'Missing user_id parameter'}, status=400)
        
        try:
            current_time = datetime.now()
            opened_status_ids = get_status_ids_from_assigned_side(user_id)
            
            
            task_content_type = ContentType.objects.get_for_model(TaskHierarchy)
            # Get the IDs of tasks that have future scheduled times in ReminderToSchedule
            future_scheduled_task_ids = ReminderToSchedule.objects.filter(
                user_id=user_id,
                content_type=task_content_type,
                scheduled_time__gt=current_time
            ).values_list('object_id', flat=True)
        
        
        
            tasks = TaskHierarchy.objects.filter(
                Q(status__id__in=opened_status_ids),
                ~Q(id__in=future_scheduled_task_ids), 
                Q(due_date__lte=current_time),
                Q(created_by_id=user_id) | Q(assign_to__id=user_id),
                is_personal=False,
                inTrash=False
            ).distinct().order_by('due_date')

            user_serializer = TaskHierarchyForRescheduleSerializer(tasks, many=True)
            return JsonResponse({'success': True, 'status': 200, 'data': user_serializer.data}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return JsonResponse({'success': False, 'status': 'Error retrieving tasks', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    
    @csrf_exempt
    def re_schedule_event(self, request):

        
        user_id = request.POST.get('user_id')
        category = request.POST.get('category')
        object_id = request.POST.get('object_id')
        slot_id = request.POST.get('slot_id')

        if not all([user_id, category, object_id, slot_id]):
            return JsonResponse({'success': False, 'message': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            slot = UserWorkSlot.objects.get(id=slot_id)
            date = slot.user_work_schedule.date.strftime('%Y-%m-%d')
            start_time = slot.slot.split(' - ')[0]  # Extract the start time
            scheduled_time_str = f"{date} {start_time}"
            scheduled_time = parse_datetime(scheduled_time_str)

            if scheduled_time is None:
                raise ValueError("Invalid datetime format")

        except UserWorkSlot.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Slot not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if category == 'task':
                content_type = ContentType.objects.get_for_model(TaskHierarchy)
            elif category == 'meeting':
                content_type = ContentType.objects.get_for_model(Meettings)
            else:
                return JsonResponse({'success': False, 'message': 'Invalid category'}, status=status.HTTP_400_BAD_REQUEST)

            reminder = ReminderToSchedule.objects.create(
                user_id=user_id,
                content_type=content_type,
                object_id=object_id,
                scheduled_time=scheduled_time,
                calendar_reminder=None  # Handle calendar reminder if needed
            )

            slot.freeze = True
            slot.save()

        except Exception as e:
            return JsonResponse({'success': False, 'message': f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return JsonResponse({'success': True, 'message': 'Reminder scheduled successfully'}, status=status.HTTP_201_CREATED)
        


    @csrf_exempt
    def get_category_wise_event(self, request):
        try:
            user_id = request.GET.get('user_id')
            category = request.GET.get('category')
            object_id = request.GET.get('object_id')
            summery = request.GET.get('summery')
            print(category, object_id)
        
            if user_id:
                if category and object_id:
                    if category=='Event':
                        obj = Events.objects.filter(id=object_id)
                        serializer = GetSpecificEventsSerializer(obj, many=True)
                    
                    elif category=='Task':
                        obj = TaskHierarchy.objects.filter(id=object_id)
                        serializer = GetSpecificTaskHierarchySerializer(obj, many=True)
                    
                    elif category=='Meeting':
                        obj = Meettings.objects.filter(id=object_id).first()
                        if summery == 'true' or summery == True or summery == "True":  # Check if summery is true
                            meeting_data = GetSpecificMeetingCalenderSerializer(obj).data
                            meeting_summary = MeettingSummery.objects.filter(meettings=obj).first()
                            if meeting_summary:
                                summary_data = MeetingSummarySerializer(meeting_summary).data
                                return JsonResponse({
                                    "success": True,
                                    "status": status.HTTP_200_OK,
                                    "message": "Calendar Reminder with Meeting Summary retrieved successfully",
                                    "data": meeting_data,
                                    "summery":summary_data 
                                })
                            else:
                                return JsonResponse({
                                    "success": True,
                                    "status": status.HTTP_200_OK,
                                    "message": "retrieved successfully",
                                    "data": meeting_data
                                })
                        else:
                            serializer = GetSpecificMeetingCalenderSerializer(obj)
                        
                    elif category== 'Consultation':
                        obj = DoctorConsultation.objects.filter(id=object_id)
                        serializer = GetSpecificDoctorConsultationSerializer(obj, many=True)
                    
                    return JsonResponse({
                        "success": True,
                        "status": status.HTTP_200_OK,                
                        "message": "Calender Reminder retrieved successfully",
                        "data":  serializer.data
                    })
                else:
                    return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,                
                    "message": "Missing 'user_id' parameter"
                })
            else:
                return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,                
                "message": "Missing 'user_id' parameter"
            })
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    @csrf_exempt
    def update_events(self, request):
        try:
            user_id = request.data.get('user_id')
            category = request.data.get('category')
            obj_id = request.data.get('id')
            print(user_id, category, obj_id)

            if not user_id or not category or not obj_id:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Invalid request. user_id, category, and id are required."
                })

            user = User.objects.get(id=user_id)

            if category == 'Event':
                try:
                    event = Events.objects.get(id=obj_id, user_id=user)
                    eventSerialData = EventCalenderSerializer(event, data=request.data)
                    if eventSerialData.is_valid(raise_exception=True):
                        save_event = eventSerialData.save()

                        guest_ids = request.data.get('guest_ids', ',')
                        guest_user_ids = [int(id) for id in guest_ids.split(',') if id]
                        guest_users = User.objects.filter(id__in=guest_user_ids)
                        event.guest.set(guest_users)
                        event.save()
                        

                        return JsonResponse({
                            "success": True,
                            "status": status.HTTP_200_OK,
                            "message": "Event updated successfully",
                            "data": EventCalenderSerializer(save_event).data
                        })
                except Events.DoesNotExist:
                    pass

            elif category == 'Meeting':
                try:
                    meeting = Meettings.objects.get(id=obj_id, user_id=user)
                    meetingSerialData = MeetingCalenderSerializer(meeting, data=request.data)
                    if meetingSerialData.is_valid(raise_exception=True):
                        save_meeting = meetingSerialData.save()

                        participent_ids = request.data.get('participent_ids', ',')
                        participent_user_ids = [int(id) for id in participent_ids.split(',') if id]
                        participent_users = User.objects.filter(id__in=participent_user_ids)

                        
                        meeting.participant.set(participent_users)
                        meeting.save()

                        return JsonResponse({
                            "success": True,
                            "status": status.HTTP_200_OK,
                            "message": "Meeting updated successfully",
                            "data": MeetingCalenderSerializer(save_meeting).data
                        })
                except Meettings.DoesNotExist:
                    pass


            elif category == 'Task':
                try:
                    task = TaskHierarchy.objects.get(id=obj_id, created_by=user)
                    taskSerialData = TaskHierarchyCalenderSerializer(task, data=request.data)
                    if taskSerialData.is_valid(raise_exception=True):
                        assigned = request.data.get('assign_to', ',')
                        assign_user_ids = [int(id) for id in assigned.split(',') if id]
                        assign_users = User.objects.filter(id__in=assign_user_ids)
                        task.assign_to.clear()
                        task.assign_to.set(assign_users)
                        save_task = taskSerialData.save()
                        

                        return JsonResponse({
                            "success": True,
                            "status": status.HTTP_200_OK,
                            "message": "Task updated successfully"
                        })
                except TaskHierarchy.DoesNotExist:
                    pass

            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": f"No {category} found with the given ID for the user."
            })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found"
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update object",
                "errors": str(e)
            })