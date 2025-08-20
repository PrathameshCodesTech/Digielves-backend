
from digielves_setup.models import DueRequest, Notification, SubTaskChild, SubTasks, TaskAction, Tasks, User , notification_handler
from employee.seriallizers.request_seiallizers import GetRequestSerializer
from employee.seriallizers.subtaskchild_seriallizers import CreateSubTaskChildSerializer, GetSubTaskChildSerializer
from employee.views.controllers.status_controllers import get_status_ids_from_creater_side
from rest_framework import viewsets
from rest_framework.decorators import action
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from django.db.models.signals import post_save
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from datetime import datetime
import pytz
class RequestViewSet(viewsets.ModelViewSet):
    
    
    @csrf_exempt
    def make_request(self, request):
        try:
            # Get the sender user
            user_id = request.POST.get('user_id')
            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "user_id is required."
                })
            user1 = User.objects.get(id=user_id)

            # Get the task
            task_id = request.POST.get('task_id')
            request_from = request.POST.get('request_from')
            if not task_id:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "task_id is required."
                })
            

            task, prefix = None, "task"
            if request_from == "subtask":
                task = SubTasks.objects.get(id=task_id)
                prefix = "Sub task"
                
            elif request_from == "subtaskchild":
                task = SubTaskChild.objects.get(id=task_id)
                prefix = "Sub task child"
            else:
                task = Tasks.objects.get(id=task_id)
                prefix = "task"
            if not task:
                return JsonResponse({
                    "success": False,
                    "status": 404,
                    "message": "Task not found."
                })
            
            # Create the request
            due_request = DueRequest.objects.create(
                sender=user1,
                receiver=task.created_by,
                task=task if request_from == "task" else None,
                subtasks=task if request_from == "subtask" else None,
                subtaskchild=task if request_from == "subtaskchild" else None,
                current_due_date=task.due_date,
                proposed_due_date=request.POST.get('due_date')
            )
            timezone = pytz.timezone('Asia/Kolkata')

            # Format current due date without the timezone offset
            current_due_date_str = task.due_date.replace(tzinfo=pytz.utc).astimezone(timezone).strftime('%Y-%m-%d %H:%M:%S') if task.due_date else "None"

            # Format proposed due date without the timezone offset
            proposed_due_date_str = datetime.strptime(request.POST.get('due_date'), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')

            remark=f"Request to change due date for {prefix.lower()} '{task.task_topic}' from {current_due_date_str} to {proposed_due_date_str}."

            TaskAction.objects.create(
                                    user_id=user1,
                                    task=task if request_from=="task" else task.Task if request_from == "subtask" else task.subtasks.Task if request_from == "subtaskchild" else None,
                                    remark=remark
                                )
            # Create notification
            post_save.disconnect(notification_handler, sender=Notification)
            
            notification_msg = f"{user1.firstname} {user1.lastname} has requested a due date change for the task '{task.task_topic}'"
            action_content_type = ContentType.objects.get_for_model(DueRequest)
            
            notification = Notification.objects.create(
                user_id=user1,
                where_to="request",
                notification_msg=notification_msg,
                action_content_type=action_content_type,
                action_id=due_request.id,
            )
            
            notification.notification_to.add(task.created_by)
            
            post_save.connect(notification_handler, sender=Notification)
            post_save.send(sender=Notification, instance=notification, created=True)

            return JsonResponse({
                "success": True,
                "status": 201,
                "message": "Request created successfully."
            })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": "User not found."
            })

        except (Tasks.DoesNotExist, SubTasks.DoesNotExist, SubTaskChild.DoesNotExist):
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": "Task not found."
            })

        except ContentType.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": "Content type not found."
            })

       
    @csrf_exempt
    def get_requests(self, request):
        user_id = request.GET.get('user_id')

        try:
            user_instance = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found",
            })


        sub_task = DueRequest.objects.filter(receiver=user_instance, inTrash = False)
        
        print(sub_task)
        serializer = GetRequestSerializer(sub_task, many=True)

        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,
            "data": serializer.data
        })
    
    @csrf_exempt
    def update_request(self, request):
        try:
            request_id = request.POST.get('request_id')
            status_value = request.POST.get('status')
            user_id = request.POST.get('user_id')

            if not request_id or not status_value or not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Missing request_id, status, or user_id."
                })

            user_instance = User.objects.filter(id=user_id).first()
            if not user_instance:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "User not found."
                })

            due_request = DueRequest.objects.filter(id=request_id, receiver=user_instance).first()
            if not due_request:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "DueRequest not found."
                })

            timezone = pytz.timezone('Asia/Kolkata')
            # Determine task and update due date if approved
            task = due_request.task or due_request.subtasks or due_request.subtaskchild
            if status_value == "1":  # "1" means "approved"
                due_request.status = "approved"
                task.due_date = due_request.proposed_due_date
                task.save()
                action_remark = "accepted"
                updated_due_date = task.due_date.replace(tzinfo=pytz.utc).astimezone(timezone).strftime('%Y-%m-%d %H:%M:%S') if task.due_date else "None"
                due_date_remark = f" The due date has been updated to {updated_due_date}."
                notification_msg = f"{user_instance.firstname} {user_instance.lastname} has approved your due date change request for the task '{task.task_topic}'"
            else:
                due_request.status = "rejected"
                action_remark = "rejected"
                updated_due_date = None
                due_date_remark = ""
                notification_msg = f"{user_instance.firstname} {user_instance.lastname} has rejected your due date change request for the task '{task.task_topic}'"


            prefix = "task" if due_request.task else "sub task" if due_request.subtasks else "sub task child"
            remark = f"Request to change due date for {prefix.lower()} '{task.task_topic}' has been {action_remark}.{due_date_remark}"
            TaskAction.objects.create(
                user_id=user_instance,
                task=task if due_request.task else task.Task if due_request.subtasks else task.subtasks.Task,
                remark=remark
            )
            
            
            post_save.disconnect(notification_handler, sender=Notification)
            notification = Notification.objects.create(
                user_id=user_instance,
                where_to="request",
                notification_msg=notification_msg,
                action_content_type=ContentType.objects.get_for_model(DueRequest),
                action_id=due_request.id
            )
            notification.notification_to.add(due_request.sender)
            post_save.connect(notification_handler, sender=Notification)
            post_save.send(sender=Notification, instance=notification, created=True)

            due_request.save()

            return JsonResponse({
                "success": True,

            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "errors": str(e),
            })


    
    @csrf_exempt
    def delete_request(self, request):
        request_id = request.GET.get('request_id')
        user_id = request.GET.get('user_id')

        if not request_id  or not user_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Missing request_id, status, or user_id."
            })

        try:
            user_instance = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found."
            })

        try:
            due_request = DueRequest.objects.get(id=request_id, receiver=user_instance)
        except DueRequest.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "DueRequest not found."
            })
        due_request.inTrash = True
        due_request.save()
        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK
            })  