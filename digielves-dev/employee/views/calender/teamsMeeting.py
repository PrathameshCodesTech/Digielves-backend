from asyncio import Event
from django.http import JsonResponse

from configuration.gzipCompression import compress
from digielves_setup.models import Events, Meettings, Tasks, User,MeettingSummery
from employee.seriallizers.calender.calender_seriallizaers import CombinedEventMeetingSerializer, CombinedEventMeetingSerializerOnly, EventCalenderDashboardSerializer, EventCalenderSerializer, MeetingCalenderDashboardSerializer, MeetingCalenderSerializer, TasksCalenderSerializer
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

from configuration.createTeamsMeeting import create_teams_meeting

from configuration.zoom_utils import get_zoom_access_token

from django.shortcuts import get_object_or_404




     


class teamsViewset(viewsets.ModelViewSet):
    @csrf_exempt
    def createTeamMeeting(self,request):
    
        agenda = request.data.get('agenda')
        start_time = request.data.get('start_time')
        users = []
        
        
        try:
            response = create_teams_meeting(agenda, start_time, users )

            response = {
            "success": True,
            "status": 201,
            "message": "Meeting Created Successfully",
            "data": [{"meet_link":response[0],"uuid":response[1] ,"meet_id":response[2]}]
            }
            return JsonResponse(response)

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