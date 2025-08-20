
from configuration.gzipCompression import compress
from digielves_setup.models import TaskComments, Tasks, User
from employee.seriallizers.task_seriallizers import TaskChatSerializer

from employee.seriallizers.template_seriallizers import *
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import status
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from django.db.models import Value, F
from django.db.models.functions import Concat
class TaskCommentViewSet(viewsets.ModelViewSet):

    @csrf_exempt
    def createTaskComment(self, request):
        try:
            task_id = request.POST.get('task_id')
            user_id = request.POST.get('user_id')
            comment = request.POST.get('comment')

            if not task_id or not user_id or not comment:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. One or more fields are missing."
                })

            task = Tasks.objects.filter(id=task_id).first()
            user = User.objects.filter(id=user_id).first()

            if not task or not user:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task or sender not found."
                })

            task_comment = TaskComments(task=task, user_id=user, comment=comment)
            task_comment.save()

           

            response = {
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Task Comment created successfully.",
                
            }

            return JsonResponse(response)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to create Task Comment.",
                "errors": str(e)
            })
            
    @csrf_exempt
    def get_task_comments(self,request):
        try:
            task_id = request.GET.get('task_id')
            user_id = request.GET.get('user_id')
            

            if not task_id and not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id is missing."
                })

            
            
            # task_actions = TaskAction.objects.filter(task_id=task_id).select_related('user_id').values(
            #     'user_id','user_id__firstname', 'user_id__lastname', 'task_id', 'remark', 'created_at'
            # ).annotate(username=F('user_id__firstname') + Value(' ') + F('user_id__lastname'))

            task_actions = TaskComments.objects.filter(task_id=task_id).select_related('user_id').values(
            'task_id', 'created_at'
        ).annotate(username=Concat('user_id__firstname', Value(' '), 'user_id__lastname'), sender_id=F('user_id'),message=F('comment'))
            
            
            sorted_date = sorted(task_actions, key=lambda x: x['created_at'])


            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task actions and chats retrieved successfully.",
                "data": sorted_date
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve task actions and chats.",
                "errors": str(e)
            })