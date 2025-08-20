from django.template import Template
from digielves_setup.models import Board, Checklist, TaskAction, Tasks, User
from employee.seriallizers.task_seriallizers import TaskActionSerializer, TaskGetSerializer

from employee.seriallizers.template_seriallizers import *
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import status
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

class TaskActionViewSet(viewsets.ModelViewSet):
    @csrf_exempt
    def createTaskAction(self, request):
        try:
            user_id = request.data.get('user_id')
            task_id = request.data.get('task_id')
            current_status = request.data.get('current_status')
            remark = request.data.get('remark')
            check_id = request.data.get('check_id')

            if not user_id or not task_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. Required fields are missing."
                })

            user = User.objects.filter(id=user_id).first()
            if not user:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "User not found."
                })

            task = Tasks.objects.filter(id=task_id).first()
            if not task:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task not found."
                })
            # print(task.created_by.id)
            # print(user_id)
            # if task.assign_to != user_id and task.created_by.id != user_id:
            #     return JsonResponse({
            #         "success": False,
            #         "status": status.HTTP_401_UNAUTHORIZED,
            #         "message": "You don't have access to perform this action on the task."
            #     })

            # Construct the remark based on provided current_status and previous status
            if current_status:
                prev_status = task.status
                remark = f"change the status {prev_status} to {current_status}"
            else:
                prev_status = None



            if check_id:
                try:
                    prev_checklist = Checklist.objects.get(id=check_id)
                    current_checklist = task.checklist
                    prev_checklist_name = prev_checklist.name
                    current_checklist_name = current_checklist.name
                    remark = f"move this task from {current_checklist_name} to {prev_checklist_name}"
                except Checklist.DoesNotExist:
                    pass
            task_action = TaskAction(user_id=user, task=task, remark=f"{user.firstname} {user.lastname} {remark}")
            task_action.save()


            try:
                task = Tasks.objects.get(id=task_id)
                task_serializer = TaskGetSerializer(task)

                task_actions = TaskAction.objects.filter(task_id=task_id)
                task_actions_serializer = TaskActionSerializer(task_actions, many=True)


                response_data = {
                    "task": task_serializer.data,
                    "task_actions": task_actions_serializer.data
                }

                return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task and TaskActions retrieved successfully.",
                "data": response_data
            })
            except Exception as e:
                print("e")
                pass

            return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Task action created successfully.",
                "data": {
                    "id": task_action.id,
                    "user_id": task_action.user_id.id,
                    "task_id": task_action.task.id,
                    
                    "remark": task_action.remark,
                    "created_at": task_action.created_at
                }
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to create task action.",
                "errors": str(e)
            })
        
    @csrf_exempt
    def getTaskWithActions(self, request):
        task_id = request.GET.get('task_id')
        if not task_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. task_id is missing."
            })
        
        try:
            task = Tasks.objects.get(id=task_id)
            task_serializer = TaskGetSerializer(task)

            task_actions = TaskAction.objects.filter(task_id=task_id)
            task_actions_serializer = TaskActionSerializer(task_actions, many=True)

            response_data = {
                "task": task_serializer.data,
                "task_actions": task_actions_serializer.data
            }

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task and TaskActions retrieved successfully.",
                "data": response_data
            })

        except Tasks.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Task not found.",
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve Task and TaskActions.",
                "errors": str(e)
            })
