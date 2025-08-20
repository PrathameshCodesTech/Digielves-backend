from asyncio import Event
from django.http import JsonResponse

from configuration.gzipCompression import compress
from digielves_setup.models import CalenderReminder, ReminderToSchedule, SubTaskChild, SubTasks, DoctorConsultation, Events, Meettings, Tasks, User,MeettingSummery, Notification, Redirect_to, notification_handler
from digielves_setup.send_emails.email_conf.send_meet_link import sendMeetLink 
from employee.seriallizers.calender.calender_seriallizaers import CalenderReminderSerializer, CombinedEventMeetingSerializer, CombinedEventMeetingSerializerOnly, EventCalenderDashboardSerializer, EventCalenderSerializer, MeetingCalenderDashboardSerializer, MeetingCalenderSerializer, TasksCalenderSerializer
from employee.seriallizers.calender.event_seriallizers import EventSerializers

from employee.seriallizers.calender.meeting_seriallizers import MeetingSerializer, Meettingerializer, MeetingGetSerializer, MeettingSummerySerializer
from employee.seriallizers.task_seriallizers import TaskGetSerializer, TaskSerializer

from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from datetime import date as python_date
import requests
import json
import os
import uuid
import requests
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from transformers import pipeline
import re
from requests.auth import HTTPBasicAuth
import threading
import time
from datetime import datetime, timedelta
from configuration.onboardingEmail import sendMail

from configuration.zoom_utils import get_zoom_access_token
from configuration.teamsMeetingRecording import getTeamsRecording

from django.http import StreamingHttpResponse
from django.contrib.contenttypes.models import ContentType

from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
import pytz 
from django.db.models.signals import post_save
import math
class MeetingViewset(viewsets.ModelViewSet):


    serializer_class = Meettingerializer
    
    def calculate_remaining_weekdays(self, from_date, to_date, included_weekdays):
        current_date = from_date
        remaining_weekdays = []

        while current_date <= to_date:
            if current_date.weekday() in included_weekdays:
                remaining_weekdays.append(str(current_date))
            current_date += timedelta(days=1)

        return remaining_weekdays

    @csrf_exempt
    def createMeeting(self, request):
        try:
            print(request.data)
            meet_serial_data = Meettingerializer(data=request.data)
            if not meet_serial_data.is_valid():
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid data",
                    "errors": meet_serial_data.errors
                })

            meet = meet_serial_data.save()
            meet_link = request.data.get('meet_link')
            email_list = [email.strip() for email in request.data.get('email',',').split(',')]
            participent_ids = request.data.get('participent_ids', ',')
            participent_user_ids = [int(user_id) for user_id in participent_ids.split(',') if user_id.strip()]
           
            user_info = User.objects.get(id=request.data.get('user_id'))
            f_name=f"{user_info.firstname} {user_info.lastname}"
            if participent_user_ids:
                meet.participant.set(participent_user_ids)
                
 
            valid_emails_in_org = [email for email in email_list if email and '@' in email]
            if valid_emails_in_org:
                
                
                
                t = threading.Thread(target=thread_to_send_meet_link, args=(email_list, meet_link, meet.from_date, meet.from_time, f_name, meet.title))

                t.setDaemon(True) 
                t.start() 
            

            other_list = [email.strip() for email in request.data.get('other_emails').split(',')]
            if other_list:
                meet.other_participant_email = ','.join(other_list)
            meet.save()

            valid_emails = [email for email in other_list if email and '@' in email]
            if valid_emails:
                
                
                t = threading.Thread(target=thread_to_send_meet_link, args=(other_list, meet_link, meet.from_date, meet.from_time, f_name, meet.title))

                t.setDaemon(True) 
                t.start() 
                # for other_email in other_list:
                #     print("-------------------------------hmmmm")
                    
                #     sendMeetLink(other_email, meet_link,meet.from_date,meet.from_time,f"{user_info.firstname} {user_info.lastname}" , meet.title )

            

            other_list = [email.strip() for email in request.data.get('other_emails', ',').split(',')]
            common_attributes = {
                "user_id": meet.user_id,
                "other_participant_email": ','.join(other_list),
                "category": meet.category,
               
                "title": meet.title,
                "purpose": meet.purpose,
                "from_time": meet.from_time,
                "to_time": meet.to_time,
                "status_complete": meet.status_complete,
                "meeting_processed": meet.meeting_processed,
                "summery_got": meet.summery_got
            }

            # Create a notification for the entire meeting
            try:
                post_save.disconnect(notification_handler, sender=Notification)
                notification = Notification.objects.create(
                    user_id=request.user,
                    where_to="meet",
                    notification_msg=f"You have been assigned a meet: {meet.title}",
                    action_content_type=ContentType.objects.get_for_model(Meettings),
                    action_id=meet.id
                )
                
                print("----------------------------in notiii")
                print(participent_user_ids)
                notification.notification_to.set(participent_user_ids)
                post_save.connect(notification_handler, sender=Notification)
                post_save.send(sender=Notification, instance=notification, created=True)
                Redirect_to.objects.create(notification=notification, link="/employee/meeting")
                
            except Exception as e:
                print("Notification creation failed:", e)
            repeat_meeting = request.data.get('repeat_meeting')
            
            
            if repeat_meeting=="true":
                
                
                
                start_date_str = request.data.get('from_date')
                end_date_str = request.data.get('to__date')
                
                included_weekdays_str = request.data.get('included_weekdays', '')

                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

                included_weekdays = [int(day) for day in included_weekdays_str.split(',') if day]
                remaining_weekdays = self.calculate_remaining_weekdays(start_date, end_date, included_weekdays)
                    
                for remaining_date_str in remaining_weekdays[1:]:
                    
                    print("-----------------at this11")
                    remaining_date = datetime.strptime(remaining_date_str, '%Y-%m-%d').date()
                    links_list=create_zoom_meeting_seprate_func(meet.title,remaining_date_str)
                    print("---------------------hey hey")
                    print(links_list)
                    print(links_list[0])
                    print(links_list[1])
                    print(links_list[2])
                    new_meeting = Meettings.objects.create(from_date=remaining_date, **common_attributes)
                    new_meeting.meet_link=links_list[0]
                    new_meeting.uuid=links_list[1]
                    new_meeting.meet_id=links_list[2]
                    new_meeting.participant.set(participent_user_ids)
                    new_meeting.save()
                    
                    if valid_emails:
                      
                        
                        t = threading.Thread(target=thread_to_send_meet_link, args=(other_list, new_meeting.meet_link, remaining_date, meet.from_time, f_name, meet.title))

                        t.setDaemon(True) 
                        t.start() 
                    if valid_emails_in_org:
                
                        
                        
                        t = threading.Thread(target=thread_to_send_meet_link, args=(email_list, new_meeting.meet_link, remaining_date, meet.from_time, f_name, meet.title))

                        t.setDaemon(True) 
                        t.start() 
            else:
                print("-------------hhh")
                
                pass

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



            
#    @csrf_exempt
#    def getMeeting(self, request):
#        user_id = self.request.GET.get('user_id')
#
#        queryset = Meettings.objects.filter(Q(user_id=user_id) | Q(participant=user_id)).distinct()
#        print(queryset)
#    
#        serializer = MeetingGetSerializer(queryset, many=True)
#        
#    
#        return JsonResponse({
#            "success": True,
#            "status": 200,
#            "message": "Meetings retrieved successfully",
#            "data": serializer.data
#        })


    @csrf_exempt
    def getMeeting(self, request):
        user_id = self.request.GET.get('user_id')
        current_datetime = timezone.now()

        queryset = Meettings.objects.filter(
            Q(user_id=user_id) | Q(participant=user_id)
        ).distinct()

        current_and_future_meetings = []
        past_meetings = []

        for meeting in queryset:
            if meeting.from_date and meeting.from_time:
                meeting_datetime = datetime.combine(meeting.from_date, meeting.from_time)
                if timezone.is_naive(meeting_datetime):
                    meeting_datetime = timezone.make_aware(meeting_datetime, timezone.get_current_timezone())

                if meeting_datetime >= current_datetime:
                    current_and_future_meetings.append(meeting)
                else:
                    past_meetings.append(meeting)

        current_and_future_meetings.sort(key=lambda x: (x.from_date, x.from_time))
        past_meetings.sort(key=lambda x: (x.from_date, x.from_time))

        sorted_meetings = current_and_future_meetings + past_meetings

        meetings_data = []

        for meeting in sorted_meetings:
            meeting_data = MeetingGetSerializer(meeting).data
            meeting_summery = None

            if meeting.meeting_processed:
                meeting_summery = MeettingSummery.objects.filter(meettings=meeting).last()

            meeting_summery_data = "empty"
            if meeting_summery:
                meeting_summery_data = {
                    "meet_transcript": meeting_summery.meet_transcript,
                    "meet_audio": meeting_summery.meet_audio,
                    "meet_video": meeting_summery.meet_video,
                    "meet_summery": meeting_summery.meet_summery,
                    "meet_tasks": meeting_summery.meet_tasks,
                }

            meeting_data["meeting_summery_task"] = meeting_summery_data
            meetings_data.append(meeting_data)

        return JsonResponse({
            "success": True,
            "status": 200,
            "message": "Meetings retrieved successfully",
            "data": meetings_data
        })

    
    
    
    @csrf_exempt
    def update_meeting_status(self,request):

        try:
        
            user_id = request.POST.get('user_id')
            meeting_id = request.POST.get('meeting_id')
            meet_link_id = request.POST.get('meet_id')
            print("--------------------------------")
            print(meeting_id)
            print(meet_link_id)
 

                
            t = threading.Thread(target=meeting_status_update, args=(meeting_id,user_id))
            t.setDaemon(True) 
            t.start() 
                
                

    
            return JsonResponse({
                "success": True,
                "status": 200,
                "message": "Meeting status updated successfully",
            })
    
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 400,
                "message": str(e),
            })
            
    
    @csrf_exempt
    def generate_summery(self,request):
        meet_id = request.POST.get('meet_id')
        user_id = request.POST.get('user_id')
        
        
        print(meet_id)
        print(user_id)
    
        try:
            meettings_instance = Meettings.objects.get(id=meet_id)
            meettings_instance.meeting_processed = True
            meettings_instance.save()
            meetting_summaries = MeettingSummery.objects.filter(meettings=meettings_instance)
            serializer = MeettingSummerySerializer(meetting_summaries, many=True)
            
             
#            if serializer.data ==[]:
#                print("hey i am empty")
            
            print("heyy00000000000000000000000000000000000000000000000000")
            print('microsoft.com' in meettings_instance.meet_link)
            
            
            if 'microsoft.com' in meettings_instance.meet_link:
                
                print("------hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh----------------------yahhh")
                t = threading.Thread(target=getTeamsRecording, args=(meettings_instance.meet_id,meet_id))
                t.setDaemon(True) 
                t.start() 
            else:
                print("----------------------------something--------------------")
                t = threading.Thread(target=long_process, args=(meettings_instance.meet_id,meet_id))
                t.setDaemon(True) 
                t.start()
            
            return JsonResponse({
            "success": True,
            "status": 200,
            "message": "Summery Generating ...",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 400,
                "message": str(e),
            })
            
    
    



    @csrf_exempt
    def download_meeting_video(self,request):

        try:
            meeting_id = request.GET.get('meeting_id')
            fetch_meet = MeettingSummery.objects.filter(meettings=meeting_id).values('meet_video').last()
            print(fetch_meet)
            video_url = fetch_meet['meet_video']

            with open(settings.MEDIA_ROOT  + '/' + video_url, "rb") as f:
                response = StreamingHttpResponse(f.read(), content_type="video/mp4")
                response["Content-Disposition"] = f"attachment; filename=MeetingVideo.mp4"
                return response
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 400,
                "message": str(e),
            })

            



def long_process(meet_id,ids):
    try:
        print("lagnalu------373 line meetings.py")
        print(meet_id)
        zoom_api_url = f"https://api.zoom.us/v2/meetings/{meet_id}/recordings"

        zoom_api_token = get_zoom_access_token()


        headers = {
            'Authorization': f'Bearer {zoom_api_token}',
        }


        response = requests.get(zoom_api_url, headers=headers)
        print("-----hey")
        a=response.json
        print(a)
        
        if response.status_code == 200:
            data = response.json()
            print(data)


            last_recording = data['recording_files'][-1]
            audio_recording = data['recording_files'][-3]  
            video_recording = data['recording_files'][0]

            
            response = requests.get(last_recording['download_url'],headers=headers)
            response_recording = requests.get(audio_recording['download_url'],headers=headers)
            response_video_recording = requests.get(video_recording['download_url'],headers=headers)

            audio_path=""
            transcript_path=""
            video_path = ""
            print(response_recording)


            if response_video_recording.status_code == 200:
                try:
                    extension = video_recording['file_extension']
                    video_path =f'employee/video_recording/{meet_id}_zoom.{extension.lower()}'
                    save_path = os.path.join(settings.MEDIA_ROOT, f'employee/video_recording/{meet_id}_zoom.{extension.lower()}')
                    print(save_path)
      
                    with open(save_path, 'wb') as file:
                        file.write(response_video_recording.content)
                
                except Exception as e:
                    print("---------422line meeting.py")
                    print(e)
            else:
                print("Error downloading recording.")
            
            
            if response_recording.status_code == 200:
                try:
                    extension = audio_recording['file_extension']
                    audio_path =f'employee/audio_recording/{meet_id}.{extension.lower()}'
                    save_path = os.path.join(settings.MEDIA_ROOT, f'employee/audio_recording/{meet_id}.{extension.lower()}')
                    print(save_path)
    
                    with open(save_path, 'wb') as file:
                        file.write(response_recording.content)
                except Exception as e:
                    print("---------438line meeting.py")
                    print(e)
                
                
                
            else:
                print("Error downloading recording.")
    
            
            
            
            if response.status_code == 200:
                try:

                    extension = last_recording['file_extension']
                    transcript_path = f'employee/transcript/{meet_id}.{extension.lower()}'
                    save_path = os.path.join(settings.MEDIA_ROOT, f'employee/transcript/{meet_id}.{extension.lower()}')
                    print(save_path)
    
    
                    with open(save_path, 'wb') as file:
                        file.write(response.content)
                    
                    subtitles = read_vtt_file(save_path)
                    print(subtitles)
        
                    transcript_text = "\n".join(subtitle['text'] for subtitle in subtitles)
                    print(transcript_text)
                    
                    
                    
                    process_transcript = re.sub(r'[^\w\s]', '', transcript_text)


                    factor = 1
                    if len(process_transcript) < 3000:
                        factor =0.6
                        
                    summary_length = round(4 * factor * math.sqrt(len(process_transcript)))
                    
                    
                    tokenizer = AutoTokenizer.from_pretrained("slauw87/bart_summarisation")
                    model = AutoModelForSeq2SeqLM.from_pretrained("slauw87/bart_summarisation")
            
                    
                    input_ids = tokenizer.encode(transcript_text, return_tensors="pt", max_length=1024, truncation=True)
            
                    
                    summary_ids = model.generate(input_ids, max_length=1200, min_length=summary_length, length_penalty=3.0, num_beams=4, early_stopping=True)
                    print("---------")
            
                    
                    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
                    
            
            
                    action_keywords = [
                "create",
                "develop",
                "design",
                "implement",
                "deliver",
                "test",
                "analyze",
                "optimize",
                "improve",
                "resolve",
                "complete",
                "project",
                "campaign",
                "report",
                "analysis",
                "proposal",
                "presentation",
                "design",
                "document",
                "code",
                "solution",
                "deadline",
                "timeline",
                "priority",
                "urgent",
                "asap",
                "within the next",
                "by the end of",
                "goal",
                "objective",
                "target",
                "outcome",
                "benefit",
                "requirement",
                "gather",
                "collect",
                "review",
                "validate",
                "approve",
                "launch",
                "monitor",
                "evaluate",
                "scale",
                "maintain",
                "document",
                "communicate",
                "brainstorm",
                "prioritize",
                "estimate",
                "decide",
                "coordinate",
                "collaborate",
                "delegate",
                "coach",
                "mentor",
                "train",
                "manage",
                "troubleshoot",
                "scale",
                "optimize",
                "automate",
                "iterate",
                "experiment",
                "learn",
                "identify",
                "assess",
                "consider",
                "recommend",
                "finalize",
                "optimize",
                "deploy",
                "administer",
                "support",
                "maintain",
                "monitor",
                "evaluate",
                "improve",
                "measure",
                "analyze",
                "report",
                "share",
                "communicate",
                "strategize",
                "plan",
                "budget",
                "forecast",
                "estimate",
                "negotiate",
                "secure",
                "partner",
                "collaborate",
                "integrate",
                "adapt",
                "evolve",
                "transform",
                "discuss",
                "report",
                "reports"
            ]
            
                    action_pattern = r"(?:\b(?:action|task|item|work|to do|asked to|suggests to|will be|will schedule|will make|discuss|shares|meeting)\b[\s:-]*[\s]*[\w\s]+)"
                    
    
                    action_pattern += "|" + "|".join(action_keywords)
            
            
            
                    action_items = []
                    summary_sentences = summary.split('.')
                    for sentence in summary_sentences:
                        print(sentence) 
                    
                        matches = re.search(action_pattern, sentence, re.IGNORECASE)  
                        try:
                            if matches.group() is not None:
                                action_items.append(sentence)
                        except:
                            inclusive = False
                    
    
                    meettings_instance = Meettings.objects.get(id=ids)
                    
                    
                    try:
                        MeettingSummery.objects.filter(meettings=meettings_instance).delete()
                        
                        MeettingSummery.objects.update_or_create(
                            meettings=meettings_instance,
                            defaults={
                                "meet_audio": audio_path,
                                "meet_video": video_path,
                                "meet_transcript": transcript_path,
                                "meet_summery": summary,
                                "meet_tasks": action_items
                            }
                        )
                        meettings_instance.summery_got=True
                        meettings_instance.save()
                    except Exception as e:
                        print("-------99999999999999999999999999--673line meeting.ddndndnd")
                        print(e)
          
                except Exception as e:
                    print("---------625line meeting.py")
                    print(e)
            else:
                print("Error downloading transcribe.")
        elif response.status_code==404:
        
            
            print("Error in Zoom API request. Status code:", response.status_code)
            
            
            
            retry_count = 0
            max_retries = 10

            while retry_count < max_retries:
                retry_count += 1

                print("Retrying API call after  minutes...")
                time.sleep(600)

                response = requests.get(zoom_api_url, headers=headers)
                if response.status_code == 200:
                    data = response.json()

            
                    last_recording = data['recording_files'][-1]
                    audio_recording = data['recording_files'][-3]  
                    video_recording = data['recording_files'][0]

                    
                    response = requests.get(last_recording['download_url'],headers=headers)
                    response_recording = requests.get(audio_recording['download_url'],headers=headers)                    
                    response_video_recording = requests.get(video_recording['download_url'],headers=headers)

                    audio_path=""
                    transcript_path=""
                    video_path = ""
                    print(response_recording)


                    if response_video_recording.status_code == 200:
                        try:
                            extension = video_recording['file_extension']
                            video_path =f'employee/video_recording/{meet_id}_zoom.{extension.lower()}'
                            save_path = os.path.join(settings.MEDIA_ROOT, f'employee/video_recording/{meet_id}_zoom.{extension.lower()}')
                            print(save_path)
            
                            with open(save_path, 'wb') as file:
                                file.write(response_video_recording.content)
                        
                        except Exception as e:
                            print("---------422line meeting.py")
                            print(e)
                    else:
                        print("Error downloading recording.")
                    
                    
                    if response_recording.status_code == 200:
                        try:
                            extension = audio_recording['file_extension']
                            audio_path =f'employee/audio_recording/{meet_id}.{extension.lower()}'
                            save_path = os.path.join(settings.MEDIA_ROOT, f'employee/audio_recording/{meet_id}.{extension.lower()}')
                            print(save_path)
            
                            with open(save_path, 'wb') as file:
                                file.write(response_recording.content)
                        except Exception as e:
                            print("---------438line meeting.py")
                            print(e)
                        
                        
                        
                        
                    else:
                        print("Error downloading recording.")
            
                    
                    
                    
                    if response.status_code == 200:
                        try:
        
                            extension = last_recording['file_extension']
                            transcript_path = f'employee/transcript/{meet_id}.{extension.lower()}'
                            save_path = os.path.join(settings.MEDIA_ROOT, f'employee/transcript/{meet_id}.{extension.lower()}')
                            print(save_path)
            
            
                            with open(save_path, 'wb') as file:
                                file.write(response.content)
                            
                            subtitles = read_vtt_file(save_path)
                            print(subtitles)
                
                            transcript_text = "\n".join(subtitle['text'] for subtitle in subtitles)
                            print(transcript_text)
                            
                            
                            process_transcript = re.sub(r'[^\w\s]', '', transcript_text)


                            factor = 1
                            if len(process_transcript) < 3000:
                                factor =0.6
                                
                            summary_length = round(4 * factor * math.sqrt(len(process_transcript)))
                            
                            
                            
                            
                            
                            tokenizer = AutoTokenizer.from_pretrained("slauw87/bart_summarisation")
                            model = AutoModelForSeq2SeqLM.from_pretrained("slauw87/bart_summarisation")
                    
                            
                            input_ids = tokenizer.encode(transcript_text, return_tensors="pt", max_length=1024, truncation=True)
                    
                            
                            summary_ids = model.generate(input_ids, max_length=1200, min_length=summary_length, length_penalty=3.0, num_beams=4, early_stopping=True)
                            print("---------")
                    
                            
                            summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
                            
                    
                    
                            action_keywords = [
                        "create",
                        "develop",
                        "design",
                        "implement",
                        "deliver",
                        "test",
                        "analyze",
                        "optimize",
                        "improve",
                        "resolve",
                        "complete",
                        "project",
                        "campaign",
                        "report",
                        "analysis",
                        "proposal",
                        "presentation",
                        "design",
                        "document",
                        "code",
                        "solution",
                        "deadline",
                        "timeline",
                        "priority",
                        "urgent",
                        "asap",
                        "within the next",
                        "by the end of",
                        "goal",
                        "objective",
                        "target",
                        "outcome",
                        "benefit",
                        "requirement",
                        "gather",
                        "collect",
                        "review",
                        "validate",
                        "approve",
                        "launch",
                        "monitor",
                        "evaluate",
                        "scale",
                        "maintain",
                        "document",
                        "communicate",
                        "brainstorm",
                        "prioritize",
                        "estimate",
                        "decide",
                        "coordinate",
                        "collaborate",
                        "delegate",
                        "coach",
                        "mentor",
                        "train",
                        "manage",
                        "troubleshoot",
                        "scale",
                        "optimize",
                        "automate",
                        "iterate",
                        "experiment",
                        "learn",
                        "identify",
                        "assess",
                        "consider",
                        "recommend",
                        "finalize",
                        "optimize",
                        "deploy",
                        "administer",
                        "support",
                        "maintain",
                        "monitor",
                        "evaluate",
                        "improve",
                        "measure",
                        "analyze",
                        "report",
                        "share",
                        "communicate",
                        "strategize",
                        "plan",
                        "budget",
                        "forecast",
                        "estimate",
                        "negotiate",
                        "secure",
                        "partner",
                        "collaborate",
                        "integrate",
                        "adapt",
                        "evolve",
                        "transform",
                        "discuss",
                        "report",
                        "reports"
                    ]
                    
                            action_pattern = r"(?:\b(?:action|task|item|work|to do|asked to|suggests to|will be|will schedule|will make|discuss|shares|meeting)\b[\s:-]*[\s]*[\w\s]+)"
                            
            
                            action_pattern += "|" + "|".join(action_keywords)
                    
                    
                    
                            action_items = []
                            summary_sentences = summary.split('.')
                            for sentence in summary_sentences:
                                print(sentence) 
                            
                                matches = re.search(action_pattern, sentence, re.IGNORECASE)  
                                try:
                                    if matches.group() is not None:
                                        action_items.append(sentence)
                                except:
                                    inclusive = False
                            
            
                            meettings_instance = Meettings.objects.get(id=ids)
                            meettings_instance.summery_got=True
                            meettings_instance.save()
                            
                            
                            
                            save_meet_summery = MeettingSummery(
                                meettings=meettings_instance,
                                meet_audio=audio_path,
                                meet_transcript=transcript_path,
                                meet_video = video_path,
                                meet_summery=summary,
                                meet_tasks=action_items
                            )
                            save_meet_summery.save()
                        except Exception as e:
                            print("---------879 line meeting.py")
                            print(e)
        
                    else:
                        print("Error downloading transcribe.")
                    break

            if retry_count >= max_retries:
                print("Max retries reached. Handle accordingly.")
        else:
            print("error Zoom API request. Status code:", response.status_code)

    except Exception as e:
        print("------")
        print(e)


     
        
def read_vtt_file(file_path):
    print("read vtt")
    subtitles = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
            
            lines = lines[1:]
            
            
            timestamp = ""
            subtitle = ""
            
            for line in lines:
                line = line.strip()
                
                
                if '-->' in line:
                    timestamp = line
                
                elif not line:
                    if timestamp and subtitle:
                        subtitles.append({"timestamp": timestamp, "text": subtitle})
                        timestamp = ""
                        subtitle = ""
                else:
                    
                    subtitle += line + " "

    except Exception as e:
        print("Error reading .vtt file:", str(e))
    
    return subtitles


class MeetingNdEventsndTaskViewset(viewsets.ModelViewSet):


    serializer_class = Meettingerializer

    
    @csrf_exempt
    def get_user_calender_reminder(self, request):
        try:
            user_id = request.GET.get('user_id')
            print(user_id)
        
            if user_id:
                obj = CalenderReminder.objects.filter(Q(user_id=user_id) | Q(shared_with_users__id=user_id)).distinct()
                serializer = CalenderReminderSerializer(obj, many=True)
                
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,                
                    "message": "Calender Reminder retrieved successfully",
                    "data": {
                        'reminders' : serializer.data
                        }
                    })
            else:
                return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,                
                "message": "Missing 'user_id' parameter"
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,                
                "message": "Calender Reminder not found",
                "error": str(e)
            })

    @csrf_exempt
    def getEventsAndMeetingsAndTask(self, request):
        
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

                
                user_tasks = Tasks.objects.filter(
                (Q(created_by=user) | Q(assign_to=user)) & Q(due_date__year=year) & Q(due_date__month=month), inTrash = False
                ).distinct()

                
                # user_Subtasks = SubTasks.objects.filter(
                # (Q(created_by=user) | Q(assign_to=user)) & Q(due_date__year=year) & Q(due_date__month=month), inTrash = False
                # ).distinct()
                
                # user_SubtaskChild = SubTaskChild.objects.filter(
                # (Q(created_by=user) | Q(assign_to=user)) & Q(due_date__year=year) & Q(due_date__month=month), inTrash = False
                # ).distinct()
                

            else:
                
                guest_events = Events.objects.filter(Q(user_id=user) | Q(guest=user)).distinct().order_by('-created_at')
                participant_meetings = Meettings.objects.filter(Q(user_id=user) | Q(participant=user)).distinct().order_by('-created_at')
                user_tasks = Tasks.objects.filter(Q(created_by=user) | Q(assign_to=user), inTrash = False).distinct()
                
                # user_Subtasks = SubTasks.objects.filter(
                #     (Q(created_by=user) | Q(assign_to=user) ), inTrash = False
                # ).distinct()
                
                # user_SubtaskChild = SubTaskChild.objects.filter(
                #     (Q(created_by=user) | Q(assign_to=user) ), inTrash = False
                # ).distinct()
                
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
    def updateEventMeetingTask(self, request):
        try:
            user_id = request.data.get('user_id')
            category = request.data.get('category')
            obj_id = request.data.get('id')

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
                        print("🐍 File: calender/meeting.py | Line: 1215 | updateEventMeetingTask ~ assign_users",assign_users)
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
    


    def delete_item(self,request):
        try:
            user_id = request.GET.get('user_id')
            category = request.GET.get('category')
            item_id = request.GET.get('id')

            user = User.objects.get(id=user_id)

            
            if category == 'Event':
                item = Events.objects.get(id=item_id, user_id=user)
            elif category == 'Meeting':
                item = Meettings.objects.get(id=item_id, user_id=user)
            elif category == 'Task':
                item = Tasks.objects.get(id=item_id, created_by=user)
            else:
                return JsonResponse({
                    "success": False,
                    "message": "Invalid category"
                }, status=400)

            
            item.delete()

            return JsonResponse({
                "success": True,
                "message": f"{category.capitalize()} deleted successfully"
            })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "User not found"
            }, status=404)

        except Events.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": f"{category.capitalize()} not found"
            }, status=404)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": "Failed to delete item",
                "error": str(e)
            }, status=500)
    



    @csrf_exempt
    def testgetEventsAndMeetingsAndTask(self, request):
        try:
            user_id = request.GET.get('user_id')
            month = request.GET.get('month')

            if user_id is None:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Invalid request. user_id is required."
                })

            user = User.objects.get(id=user_id)

            
            unique_event_ids = set()
            unique_meeting_ids = set()

            
            combined_data = []

            if month:
                
                guest_events = Events.objects.filter(
                    (Q(user_id=user) | Q(guest=user)) & Q(from_date__month=month)
                ).all()

                
                participant_meetings = Meettings.objects.filter(
                    (Q(user_id=user) | Q(participant=user)) & Q(from_date__month=month)
                ).all()
            else:
                
                guest_events = Events.objects.filter(Q(user_id=user) | Q(guest=user)).all()

                
                participant_meetings = Meettings.objects.filter(Q(user_id=user) | Q(participant=user)).all()

                user_tasks = Tasks.objects.filter(Q(created_by=user) | Q(assign_to=user)).all()

            
            for event in guest_events:
                if event.id not in unique_event_ids:
                    unique_event_ids.add(event.id)
                    combined_data.append(serialize_event(event, user))

            
            for meeting in participant_meetings:
                if meeting.id not in unique_meeting_ids:
                    unique_meeting_ids.add(meeting.id)
                    combined_data.append(serialize_meeting(meeting, user))

            
            user_tasks = Tasks.objects.filter(
                (Q(created_by=user) | Q(assign_to=user)) & Q(due_date__contains=f"-{month}-")
            ).all()


            for task in user_tasks:
                combined_data.append(serialize_task(task, user))

            response = {
                "success": True,
                "status": 200,
                "message": "Events and meetings retrieved successfully",
                "data": combined_data
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

def serialize_event(event, user):
    serializer = EventSerializers(event)
    serialized_data = serializer.data
    serialized_data = add_user_data_to_item(serialized_data, user)
    return serialized_data

def serialize_meeting(meeting, user):
    serializer = MeetingSerializer(meeting)
    serialized_data = serializer.data
    serialized_data = add_user_data_to_item(serialized_data, user)
    return serialized_data

def serialize_task(task, user):
    serializer = TaskGetSerializer(task)
    serialized_data = serializer.data
    serialized_data = add_user_data_to_item(serialized_data, user)
    return serialized_data

def add_user_data_to_item(item, user):
    return item





class DashboardViewset(viewsets.ModelViewSet):

    @csrf_exempt
    def getEventsAndMeetings(self, request):
        try:
            user_id = request.GET.get('user_id')
            date_param = request.GET.get('date')

            if user_id is None:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Invalid request. user_id is required."
                })

            user = User.objects.get(id=user_id)
            if date_param:
                try:
                    date = datetime.strptime(date_param, '%Y-%m-%d')
                except ValueError:
                    return JsonResponse({
                        "success": False,
                        "status": 400,
                        "message": "Invalid date format. Please provide the date in ISO format (YYYY-MM-DD)."
                    })
            else:
                date = timezone.now().date()

            guest_events = Events.objects.filter(
                (Q(user_id=user) | Q(guest=user)) & (Q(to_date__isnull=False, from_date__lte=date, to_date__gte=date) | Q(from_date=date))
            ).distinct()
            
            participant_meetings = Meettings.objects.filter(
                (Q(user_id=user) | Q(participant=user)) & (Q(to_date__isnull=False, from_date__lte=date, to_date__gte=date) | Q(from_date=date))
            ).distinct()
            
            
            
            doctor_consultations = DoctorConsultation.objects.filter(
                Q(doctor_id=user) | Q(employee_id=user),confirmed="1",status="Booked",
                appointment_date=date.strftime('%Y-%m-%d')
            )
            
            print(doctor_consultations)
            events_and_meetings = list(guest_events) + list(participant_meetings) 
            events_and_meetings = list(guest_events) + list(participant_meetings) + list(doctor_consultations)

            combined_serializer = CombinedEventMeetingSerializerOnly(events_and_meetings, many=True)

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
                
                
                if isinstance(item, DoctorConsultation):
                    item['appointment_date'] = item.appointment_date
                    item['reason_for_reschedule'] = item.reason_for_reschedule

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






        # user_id = request.GET.get('user_id')
    
        
        # date_param = request.GET.get('date')
    
    
        # if date_param:
        #     try:
        #         date = datetime.strptime(date_param, '%Y-%m-%d')
        #     except ValueError:
        #         response = {
        #         "success": False,
        #         "status": 400,
        #         'error': 'Invalid date format. Please use YYYY-MM-DD.'
        #         }
                
        #         return JsonResponse(response)
        # else:
        #     date = timezone.now().date()
        
        
        # events = Events.objects.filter(user_id=user_id, from_date=date)
        # meetings = Meettings.objects.filter(user_id=user_id, from_date=date)
        
        
        # events_serializer = MeetingCalenderDashboardSerializer(meetings, many=True)
        # meetings_serializer = EventCalenderDashboardSerializer(events, many=True)
        
        
        # combined_data = events_serializer.data + meetings_serializer.data
        
        
        
        # response = {
        #         "success": True,
        #         "status": 200,
        #         "message": "Events and meetings retrieved successfully",
        #         "data": combined_data
        #     }
        
        # return JsonResponse(response)



class ZoomViewset(viewsets.ModelViewSet):


    

    @csrf_exempt
    def get_zoom_access_token(self, request):
        zoom_api_url = 'https://zoom.us/oauth/token'
        grant_type = 'account_credentials'
        account_id = 'd6UPxnmvSKq5dXnHBVM3ag'
    
        zoom_username = '7n1UDqe7QOESjU0WV8J3Q'
        zoom_password = '7J0KZLG4IF5DjZ1tEFInOv0BKtEAKsUt'

        params = {
              'grant_type': 'account_credentials',
              'account_id': 'd6UPxnmvSKq5dXnHBVM3ag',
          }
        
        basic_auth = HTTPBasicAuth(zoom_username, zoom_password)
        
        
    
        try:
            
            response = requests.post(zoom_api_url, params=params,auth = basic_auth)
    
            if response.status_code == 200:
                response_data = response.json()
                access_token = response_data.get('access_token')
                return JsonResponse({'access_token': access_token})
            
            error_message = response.json() if response.headers['Content-Type'] == 'application/x-www-form-urlencoded' else response.text
            return JsonResponse({'error': error_message}, status=500)
    
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            


    @csrf_exempt
    def create_zoom_meeting(self,request):
        print("-----------fggjj----------------")
    
        agenda = request.data.get('agenda')
        start_time = request.data.get('start_time')
        #start_date = request.data.get('start_date')
        user_id = request.data.get('user_id')
        bearer_token = get_zoom_access_token()
        
        
#        hours, minutes = map(int, start_time.split(':'))
#        time_delta = timedelta(hours=hours, minutes=minutes)
#        
#        
#        parsed_date = datetime.strptime(start_date, "%Y-%m-%d")
#        
#        
#        desired_datetime = parsed_date + time_delta
#        
#        output_format = "%Y-%m-%dT%H:%M:%SZ"
#        formatted_datetime = desired_datetime.strftime(output_format)
        

        
        
        url = 'https://api.zoom.us/v2/users/me/meetings'

        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json',
        }
        
        # 'meeting_invitees': user, is remaining
      

        data = {
    'agenda': agenda,
    'default_password': False,
    'duration': 60,
    'password': '123456',
    'pre_schedule': False,
    'settings': {
    "allow_screen_sharing": True, 
    "allow_participants_to_annotate": True ,
       
        'auto_recording': 'cloud',
        'host_video': True,
        'jbh_time': 0,
        'join_before_host': True,
        'meeting_authentication': False,
        'mute_upon_entry': False,
        'waiting_room': False,
        'show_share_button':True,        
        'share_screen': True, 
        'continuous_meeting_chat': {
            'enable': True,
            'auto_add_invited_external_users': True,
        }
    },
    'start_time': start_time,
    'timezone': 'Asia/Kolkata',
    'topic': agenda,
    'type': 2,
}



        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))

            if response.status_code == 201:
                response_data = response.json()
                
                
                      
                
                response = {
            "success": True,
            "status": 201,
            "message": "Meeting Created Successfully",
            "data": [{"meet_link":response_data.get('join_url'),"uuid":response_data.get('uuid'),"meet_id":response_data.get('id')}]
        }
                return JsonResponse(response)
            else:
                response_data = response.json()
            
                print(response_data.get('code'))
                if response_data.get('code') == 124:
                    
                    
                    return JsonResponse({'erddror': response.json()}, status=500)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    


class meetSummeryViewset(viewsets.ModelViewSet):
    
    @csrf_exempt
    def get_saved_summery_and_task(self,request):
        meet_id = request.GET.get('meet_id')
        user_id = request.GET.get('user_id')
    
        try:
            meettings_instance = Meettings.objects.get(id=meet_id)
            meetting_summaries = MeettingSummery.objects.filter(meettings=meettings_instance)
            serializer = MeettingSummerySerializer(meetting_summaries, many=True)
            meettings_instance.meeting_processed = True
            meettings_instance.save()
             
            if serializer.data ==[]:
                print("hey i am empty")
                t = threading.Thread(target=long_process, args=(meettings_instance.meet_id,meet_id))
                t.setDaemon(True) 
                t.start()
            
            return JsonResponse({
                "success": True,
                "status": 200,
                "message": "Meeting summaries retrieved successfully",
                "data": serializer.data
            })
        except Meettings.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": "Meeting not found",
                "data": None
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": str(e),
                "data": None
            })


def meeting_status_update(meet_id,user_id):
    print("status updating-----")
    
    meeting=Meettings.objects.get(id = meet_id)
    meeting.meet_start_time=timezone.now()
    meeting.save() 
    time.sleep(30)

    meeting.status_complete = True
    meeting.save()

def thread_to_send_meet_link(email_list, meet_link, date,time ,full_name , title):
    
    print("thread_to_send_meet_link----------------------------")
    
    for email in email_list:
        print("-----------emelllll")
        
        
        
        sendMeetLink(email, meet_link,date,time,full_name, title )


def create_zoom_meeting_seprate_func(agenda, start_time):
    try:
        bearer_token = get_zoom_access_token()
        url = 'https://api.zoom.us/v2/users/me/meetings'

        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json',
        }

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
            'start_time': start_time,
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