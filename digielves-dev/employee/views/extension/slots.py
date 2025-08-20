import json
from configuration.createTeamsMeeting import create_teams_meeting
from configuration.gzipCompression import compress


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from configuration.zoomMeeting import create_zoom_meeting
from configuration.zoom_utils import get_zoom_access_token
from digielves_setup.models import CalenderReminder, DoctorConsultation, Events, ExtAvailableSlots, ExtAvailableSlotsTime, ExtensionDateSlot, ExtensionMeetingDateOptions, Meettings, Notification, ReminderToSchedule, SubTaskChild, SubTasks, TaskHierarchy, Tasks, User, notification_handler
# from employee.seriallizers.extension.slots_seriallizers import ExtAvailableSlotsSerializer, ExtMeettingserializer
from digielves_setup.send_emails.email_conf.send_meet_link import sendMeetLink
from employee.seriallizers.calender.calender_seriallizaers import CombinedEventMeetingSerializer
from employee.seriallizers.extension.slots_seriallizers import CombinedEventMeetingSerializerForExtension, ExtensionCalenderReminderSerializer
from employee.views.calender.meeting import create_zoom_meeting_seprate_func
from rest_framework import viewsets
from rest_framework import status
import threading
from datetime import datetime
from django.utils import timezone
import datetime as timeDelta
from django.db.models.signals import post_save
from django.contrib.contenttypes.models import ContentType
import requests
from configuration.authentication import JWTAuthenticationUser
from rest_framework.permissions import  IsAuthenticated ,AllowAny
from django.shortcuts import render
from configuration import settings
from django.template.loader import get_template
from django.http import HttpResponse
from django.http import FileResponse
from django.conf import settings
import os
from django.core.files.storage import default_storage
from django.templatetags.static import static
from django.db.models import Q

class ExtAvailableSlotsViewSet(viewsets.ModelViewSet):
    
    @csrf_exempt
    def ExtAvailableSlotsListCreate(self, request):
        user_email = request.data.get('user_email', None)
        slots_data = request.data.get('slots_data', [])

        if not user_email:
            return JsonResponse({"error": "User email is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not slots_data:
            return JsonResponse({"error": "Slots data is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            for slot in slots_data:
                date = slot.get('date', None)
                times = slot.get('time', [])

                if not date or not times:
                    continue

                # Check if an ExtAvailableSlots instance with the same user_email and date exists
                ext_available_slots, created = ExtAvailableSlots.objects.get_or_create(user_email=user_email, date=date)

                # For each time slot, check if it already exists for the given date and user email
                for time_slot in times:
                    if not ExtAvailableSlotsTime.objects.filter(ext_available_slots=ext_available_slots, time_slot=time_slot).exists():
                        # If the time slot doesn't exist, create it
                        time_instance = ExtAvailableSlotsTime.objects.create(ext_available_slots=ext_available_slots, time_slot=time_slot)
            print("🐍 File: extension/slots.py | Line: 67 | ExtAvailableSlotsListCreate ~ successfully","successfully")
            return JsonResponse(
                {
                    "success": True,
                    "message": "Slots data saved successfully"
                }, status=status.HTTP_201_CREATED)
                    

        except Exception as e:
            print("🐍 File: extension/slots.py | Line: 75 | ExtAvailableSlotsListCreate ~ e",e)
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

            
            
    # @csrf_exempt
    # def get_available_slots(self,request):
    #     user_email = request.GET.get('user_email', None)

    #     if not user_email:
    #         return JsonResponse({"error": "User email is required"}, status=status.HTTP_400_BAD_REQUEST)

    #     try:
    #         # Retrieve available slots for the user's email
    #         ext_available_slots = ExtAvailableSlots.objects.filter(user_email=user_email)

    #         # Serialize the data into the desired format
    #         slots_data = []
    #         for slot in ext_available_slots:
    #             times = slot.extavailableslotstime_set.all()
    #             if times:
    #                 for time in times:
    #                     slot_data = {
    #                         "date": slot.date,
    #                         "time": [time.time_slot]
    #                     }
    #                     slots_data.append(slot_data)

    #         response_data = {
    #             "success":True,
    #             "slots_data": slots_data
    #         }

    #         return JsonResponse(response_data, status=status.HTTP_200_OK)

    #     except Exception as e:
    #         return JsonResponse({
    #             "success":False,
    #             "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            
            
            
class CreateMeetingViewSet(viewsets.ModelViewSet):   
    
    
    # authentication_classes = [JWTAuthenticationUser]
    
    permission_classes = [AllowAny]
    
    @csrf_exempt
    def createMeetingGet(self, request):
        try:
            sender_user_info = User.objects.get(email=request.GET.get('email'))
            receiver_user_info = None
            rec_email = None

            try:
                receiver_user_info = User.objects.get(email=request.GET.get('receiver_email').replace("%40", "@"))
            except User.DoesNotExist:
                # Handle case where receiver user does not exist
                rec_email = request.GET.get('receiver_email').replace("%40", "@")
                
            datee = datetime.strptime(request.GET.get('from_date'), '%Y-%m-%d').date()
            
            platform=request.GET.get('platform')
            
            if platform == "Teams":
                create_zoom = create_teams_meeting(f"Meeting with {sender_user_info.firstname} {sender_user_info.lastname}",request.data.get('from_date'), datee)
            
            else:
                create_zoom = create_zoom_meeting_separate_fun(f"Meeting with {sender_user_info.firstname} {sender_user_info.lastname}",datee, datee)
            f_name = f"{sender_user_info.firstname} {sender_user_info.lastname}"
            from_time_str = request.GET.get('from_time')
            
            
            try:
                if len(from_time_str.split(':')) == 3:
                    from_time_str = ':'.join(from_time_str.split(':')[:2])
                # Try parsing the time string using the expected format
                from_time_obj = datetime.strptime(from_time_str, '%I:%M %p')
            except ValueError:
                try:
                    # If parsing fails, try parsing using a different format
                    from_time_obj = datetime.strptime(from_time_str, '%H:%M')
                except ValueError:
                    # If parsing still fails, handle the error or set a default value
                    print("Error: Time data does not match any expected format")
                    from_time_obj = None
            
            meeting = Meettings.objects.create(
                user_id=sender_user_info,
                title=f"Meeting with {f_name}",
                from_date=datee,
                # to_time=request.GET.get('to_time'),
                from_time =from_time_obj.time(),
                uuid=create_zoom[1],
                meet_id=create_zoom[2],
                meet_link=create_zoom[0]
            )

            

            if receiver_user_info:
                meeting.participant.add(receiver_user_info)
                
            # email_list = [email.strip() for email in request.data.get('receiver_email', ',').split(',')]
            
            # valid_emails_in_org = [email for email in email_list if email and '@' in email]
            # if valid_emails_in_org:

            t = threading.Thread(
                    target=thread_to_send_meet_link_individue,
                    args=(
                        request.GET.get('email'),
                        create_zoom[0],
                        str(request.GET.get('from_date')),
                        f"{str(request.GET.get('from_time'))}" ,  # Removed extra f-string
                        str(f_name),
                        request.GET.get('email').split("@")[0]
                    )
                )

            t.setDaemon(True)
            t.start()
            
            
            if rec_email or receiver_user_info :
                t = threading.Thread(
                    target=thread_to_send_meet_link_individue,
                    args=(
                        request.GET.get('receiver_email'),
                        create_zoom[0],
                        str(request.GET.get('from_date')),
                        f"{str(request.GET.get('from_time'))}",  # Removed extra f-string
                        str(f_name),
                        f_name
                    )
                )

                t.setDaemon(True)
                t.start()
            # print(sender_user_info.firstname, sender_user_info.lastname)
            file_path = os.path.join(settings.MEDIA_ROOT, 'email_templates', 'meeting_added.html')
            # Check if the file exists
            if os.path.exists(file_path):
                # Open and return the file as a response
                with open(file_path, 'rb') as file:
                    file_content = file.read()
                    logo_url = default_storage.url('image/calender_icon.svg')
                    # Replace placeholders with actual values
                    file_content = file_content.decode('utf-8')
                    file_content = file_content.replace('logo_placeholder',logo_url)
                    file_content = file_content.replace('full_name', f_name)
                    file_content = file_content.replace('Date', str(datee))
                    file_content = file_content.replace('time', str(request.GET.get('from_time')) )
                    return HttpResponse(file_content, content_type='text/html')
            else:
                # If the file doesn't exist, return an error response
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Template file not found",
                    "errors": "Template file not found"
                })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to add meetings",
                "errors": str(e)
            })

    @csrf_exempt
    def get_calender_extension(self, request):
        
        try:
            user_id = request.GET.get('user_id')
            email = request.GET.get('email')
            month = request.GET.get('month')
            year = request.GET.get('year')

            if user_id is None:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Invalid request. user_id is required."
                })

            user = User.objects.get(email=email)

            
            if month:
                
                guest_events = Events.objects.filter(
                    (Q(user_id=user) | Q(guest=user)) & Q(from_date__month=month)
                ).distinct()

                
                participant_meetings = Meettings.objects.filter(
                    (Q(user_id=user) | Q(participant=user)) & Q(from_date__month=month)
                ).distinct()

                
                # print(participant_meetings)

                
                user_tasks = Tasks.objects.filter(
                (Q(created_by=user) | Q(assign_to=user)) & Q(due_date__year=year) & Q(due_date__month=month), inTrash = False
                ).distinct()

                
                user_Subtasks = SubTasks.objects.filter(
                (Q(created_by=user) | Q(assign_to=user)) & Q(due_date__year=year) & Q(due_date__month=month), inTrash = False
                ).distinct()
                
                user_SubtaskChild = SubTaskChild.objects.filter(
                (Q(created_by=user) | Q(assign_to=user)) & Q(due_date__year=year) & Q(due_date__month=month), inTrash = False
                ).distinct()
                

            else:
                print("----------aabb")
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
    def get_extension_calender_reminder(self, request):
        user_id = request.GET.get('user_id')
        email = request.GET.get('user_email')
        user = User.objects.get(email = email) 
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


    
        combined_serializer = CombinedEventMeetingSerializerForExtension(events_and_meetings, many=True)
        return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,                
                "message": "Calender Reminder retrieved successfully",
                "data": {
                    'reminders' : combined_serializer.data
                    }
                })
# try:
        #     user_id = request.GET.get('user_id')
        #     email = request.GET.get('user_email')
            
        #     user_mail = User.objects.get(email = email)        
        #     # if user_id:
        #     obj = CalenderReminder.objects.filter(Q(user_id=user_mail.id) | Q(shared_with_users__id=user_mail.id)).distinct()
        #     serializer = ExtensionCalenderReminderSerializer(obj, many=True)
            
        #     return JsonResponse({
        #         "success": True,
        #         "status": status.HTTP_200_OK,                
        #         "message": "Calender Reminder retrieved successfully",
        #         "data": {
        #             'reminders' : serializer.data
        #             }
        #         })
        #     # else:
        #     #     return JsonResponse({
        #     #     "success": False,
        #     #     "status": status.HTTP_400_BAD_REQUEST,                
        #     #     "message": "Missing 'user_id' parameter"
        #     # })
        # except Exception as e:
        #     return JsonResponse({
        #         "success": False,
        #         "status": status.HTTP_400_BAD_REQUEST,                
        #         "message": "Calender Reminder not found",
        #         "error": str(e)
        #     })
    
    @csrf_exempt
    def createMeeting(self, request):
        try:
            sender_user_info = User.objects.get(email=request.data.get('sender_email'))
            receiver_user_info = User.objects.get(email=request.data.get('receiver_email'))
            print(str(request.data.get('from_date')))
            datee = datetime.strptime(request.data.get('from_date'), '%Y-%m-%d').date()
            
            create_zoom = create_zoom_meeting_separate_fun(request.data.get('from_date'), datee)
            meeting = Meettings.objects.create(
                    user_id=sender_user_info,
                    title = request.data.get('title'),
                    from_date = request.data.get('from_date'),
                    to_date = request.data.get('to_date'),
                    from_time = request.data.get('from_time'),
                    to_time = request.data.get('to_time'),
                    uuid = create_zoom[1],
                    meet_id= create_zoom[2],
                    meet_link = create_zoom[0]
                    
                )
            meeting.participant.add(receiver_user_info)
            
        
            
            email_list = [email.strip() for email in request.data.get('receiver_email',',').split(',')]
            
            
            f_name=f"{sender_user_info.firstname} {sender_user_info.lastname}"
        
                

            valid_emails_in_org = [email for email in email_list if email and '@' in email]
            
            if valid_emails_in_org:
                
                
                t = threading.Thread(target=thread_to_send_meet_link, args=(valid_emails_in_org, create_zoom[0],str(request.data.get('from_date')), str(request.data.get('from_time')), str(f_name), str(request.data.get('title'))))

                t.setDaemon(True) 
                t.start()





            # Create a notification for the entire meeting
            # try:
            #     post_save.disconnect(notification_handler, sender=Notification)
            #     notification = Notification.objects.create(
            #         user_id=request.user,
            #         where_to="meet",
            #         notification_msg=f"You have been assigned a meet: {meet.title}",
            #         action_content_type=ContentType.objects.get_for_model(Meettings),
            #         action_id=meet.id
            #     )
                
            #     print("----------------------------in notiii")
            #     print(participent_user_ids)
            #     notification.notification_to.set(participent_user_ids)
            #     post_save.connect(notification_handler, sender=Notification)
            #     post_save.send(sender=Notification, instance=notification, created=True)
            #     Redirect_to.objects.create(notification=notification, link="/employee/meeting")
                
            # except Exception as e:
            #     print("Notification creation failed:", e)
            
            
           
            return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Meetings added successfully",
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to add meetings",
                "errors": str(e)
            })
    

class AddSlotsViewSet(viewsets.ModelViewSet):   
    
    
    # authentication_classes = [JWTAuthenticationUser]
    
    permission_classes = [AllowAny]
    
    @csrf_exempt
    def add_extension_slots(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            slots_data = data.get('slots_data')
            platform = data.get('platform')

            if not email or not slots_data:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Invalid request. email and slots are required."
                })

            user = User.objects.get(email=email)

            extension_slots = []

            slots_by_date = {}
            for slot in slots_data:
                date_str = slot['start'].split('T')[0]
                if date_str not in slots_by_date:
                    slots_by_date[date_str] = []
                slots_by_date[date_str].append(slot)

            for date_str, slots in slots_by_date.items():
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                extension_date_options = ExtensionMeetingDateOptions.objects.create(
                    user=user,
                    date=date,
                    platform = platform 
                )
                for slot in slots:
                    start_time = slot.get('start').split('T')[1]
                    end_time = slot.get('end').split('T')[1]
                    slot_str = f"{start_time} - {end_time}"

                    slot_obj = ExtensionDateSlot.objects.create(
                        extension_meeting_date_options=extension_date_options,
                        slot=slot_str,
                    )
                    extension_slots.append(slot_obj)

            print("🐍 File: extension/slots.py | Line: 546 | add_extension_slots ~ successfully","successfully")
            return JsonResponse({
                "success": True,
                "status": 201,
                "message": "Extension meeting date slots created successfully.",
                "extension_slots": [{"id": slot.id, "slot": slot.slot} for slot in extension_slots]
            })
                

        except Exception as e:
            print("🐍 File: extension/slots.py | Line: 548 | add_extension_slots ~ e",e)
            return JsonResponse({
                "success": False,
                "status": 500,
                "errors": str(e)
            })

    
    @csrf_exempt
    def get_extension_slots(self, request):
        try:
            user_email = request.GET.get('user_email')

            if not user_email:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "User email is required."
                })

            user = User.objects.get(email=user_email)

            now = timezone.now()

            ten_seconds_ago = now - timeDelta.timedelta(seconds=15)

            extension_date_options = ExtensionMeetingDateOptions.objects.filter(user=user, added_date__gte=ten_seconds_ago)
            # extension_date_options = ExtensionMeetingDateOptions.objects.filter(user=user)

            slots_data = []

            unique_dates = set()  # Set to track unique dates

            for option in extension_date_options:
                option_date_str = option.date.strftime('%Y-%m-%d')
                if option_date_str not in unique_dates:
                    unique_dates.add(option_date_str)
                    slots = ExtensionDateSlot.objects.filter(extension_meeting_date_options=option)
                    slot_times = [slot.slot for slot in slots]
                    slots_data.append({
                        "date": option_date_str,
                        "slots": slot_times,
                        "platform": option.platform
                    })
            return JsonResponse({
                "success": True,
                "work_schedules": slots_data,
                # "platform": extension_date_options.platform
                
            })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": "User not found."
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "errors": str(e)
            })
        
def thread_to_send_meet_link(email_list, meet_link, date,time ,full_name , title):
    
    
    for email in email_list:

        
        
        
        sendMeetLink(email, meet_link,date,time,full_name, title )
        
def thread_to_send_meet_link_individue(email, meet_link, date,time ,full_name , title):
    

        
        
    sendMeetLink(email, meet_link,date,time,full_name, f'meeting with {full_name}' )



def create_zoom_meeting_separate_fun(agenda, start_time, time):
    try:
        bearer_token = get_zoom_access_token()
        url = 'https://api.zoom.us/v2/users/me/meetings'

        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json',
        }
   
        start_time_iso = start_time.isoformat()

        data = {
            'agenda': agenda,
            'default_password': False,
            'duration': 60,
            'password': '123456',
            'pre_schedule': False,
            'settings': {
                "allow_screen_sharing": True, 
                "allow_participants_to_annotate": True,
                'auto_recording': 'cloud',
                'host_video': True,
                'jbh_time': 0,
                'join_before_host': True,
                'meeting_authentication': False,
                'mute_upon_entry': False,
                'waiting_room': False,
                'show_share_button': True,        
                'share_screen': True, 
                'continuous_meeting_chat': {
                    'enable': True,
                    'auto_add_invited_external_users': True,
                }
            },
            'start_time': start_time_iso,
            'timezone': 'Asia/Kolkata',
            'topic': agenda,
            'type': 2,
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code == 201:
            response_data = response.json()
            print("-----------------------201  ")
            
            return [response_data.get('join_url'),response_data.get('uuid'),response_data.get('id')]
        else:
            return [0,0,0]
    except Exception as e:
        print("-----------------------exception exception")
        print(e)
        return [0,0,0]