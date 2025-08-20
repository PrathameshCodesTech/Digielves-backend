




from django.template import Template
from configuration.gzipCompression import compress
from digielves_setup.models import Board, Notification, TaskAction, TaskChatting, Tasks, User, notification_handler
from employee.seriallizers.task_seriallizers import TaskChatSerializer

from employee.seriallizers.template_seriallizers import *
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from employee.views.controllers.threads import send_notification_for_chat
from rest_framework import status
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from itertools import chain
from django.db.models import Value
from django.db.models.functions import Concat
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from configuration import settings
import os
import threading

class TaskChatViewSet(viewsets.ModelViewSet):

    @csrf_exempt
    def createTaskChatting(self, request):
        try:
            task_id = request.POST.get('task_id')
            sender_id = request.POST.get('sender_id') 
            

            if not task_id or not sender_id :
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. One or more fields are missing."
                })

            task = Tasks.objects.filter(id=task_id).first()
            print("------------check list")
            print(task.checklist)
            sender = User.objects.filter(id=sender_id).first()

            if not task or not sender:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task or sender not found."
                })

            # Check if there is a file or image upload
            if 'message' in request.FILES:
                print('Checking for file or image upload')
                message_upload = request.FILES['message']
                print(message_upload)
                file_path = os.path.join(settings.MEDIA_ROOT, 'employee/chat_files', message_upload.name)
                with open(file_path, 'wb') as destination:
                    for chunk in message_upload.chunks():
                        destination.write(chunk)

                # Create TaskChatting instance with the file path
                task_chatting = TaskChatting(task=task, sender=sender, message='employee/chat_files/'+message_upload.name)
            else:
                message_text = request.POST.get('message')
                # No file or image upload, only text message
                task_chatting = TaskChatting(task=task, sender=sender, message=message_text)
            task_chatting.save()

         
            # Check if sender is in assign_to or created_by
            
            
                
            t = threading.Thread(target=send_notification_for_chat, args=(sender,task,"chat"))
            t.setDaemon(True) 
            t.start()

                
            chats = TaskChatting.objects.filter(task=task)
            serializer = TaskChatSerializer(chats, many=True)

            response = {
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Task chatting created successfully."
                
            }

            return compress(response)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to create Task chatting.",
                "errors": str(e)
            })




    @csrf_exempt
    def getTaskChats(self, request):
        try:
            task_id = request.GET.get('task_id')
            # user_id = request.GET.get('user_id')

            if not task_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id is missing."
                })

            task = Tasks.objects.filter(id=task_id).first()
            if not task:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task not found."
                })

            chats = TaskChatting.objects.filter(task_id=task_id).values('task_id', 'sender_id', 'message', 'created_at').annotate(username=Concat('sender_id__firstname', Value(' '), 'sender_id__lastname'))
            
            for chat in chats:
                chat['created_at'] = chat['created_at'].isoformat()

            merged_data = sorted(chain(chats), key=lambda x: x['created_at'])

            

            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task chats retrieved successfully.",
                "data": merged_data
            }

            return compress(response)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve task chats.",
                "errors": str(e)
            })
