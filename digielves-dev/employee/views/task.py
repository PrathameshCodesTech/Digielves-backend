import random
from django.http import JsonResponse
import pytz
from configuration import settings
from configuration.gzipCompression import compress
from employee.seriallizers.personal_board.personal_board_seriallizers import GetPersonalTaskOnMyDaySerializer
from employee.seriallizers.user_serillizer import UserSerializer
from employee.views.controllers.status_controllers import  get_status_ids_from_assigned_side, get_status_ids_from_creater_side
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from digielves_setup.models import Checklist,TaskHierarchy, SubTaskChild, SubTasks, EmployeePersonalDetails, PersonalStatus, PersonalTask, TaskAction, TaskAttachments, TaskChatting, TaskChecklist, TaskSpecialAccess, TaskStatus, Tasks, TemplateChecklist, User, Notification, UserFilters, notification_handler
from employee.seriallizers.task_seriallizers import  SubTaskChildGetSerializer, SubTaskGetSerializer, TaskGetSerializer, TaskIndividualSerializer, TaskSerializer, TaskStatusSerializer, HierarchyTaskGetSerializer
from django.db.models import  F, Value
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from datetime import datetime, timedelta, timezone
from django.utils import timezone as newTimezone
from itertools import chain
from django.db.models.functions import Concat

# import datetime
from django.contrib.contenttypes.models import ContentType
from django.core.serializers import serialize
from django.shortcuts import get_object_or_404
from django.db.models.signals import post_save
import os
from django.core.serializers.json import DjangoJSONEncoder
import pytz
class DateTimeEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    

    @csrf_exempt
    def create_task(self, request):
        print("-------------------------------------------task")
        print(request.data)
        
        serializer = TaskSerializer(data=request.data)

        try:
            if serializer.is_valid():
            
                task = serializer.save()
                
                
                assign_user_ids = request.data['assign_to']
                assign_users = User.objects.filter(id__in=assign_user_ids)
                task.assign_to.set(assign_users)
                attachments = request.FILES.getlist('attachments') 
        
                task_attachments = []
                for attachment in attachments:
                    try:
                        
                        file_name = attachment.name
                        file_path = '/employee/task_attachment/' + file_name
                        fs = FileSystemStorage()
                        fs.save(file_path, attachment)

                       
                        task_attachment = TaskAttachments.objects.create(task=task, attachment=file_path)
                        task_attachments.append(task_attachment)
                    except Exception as e:
                        return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Failed to create Task.",
                        "errors": "Failed to process attachment: {attachment.name}. Error: {str(e)}"
                    })
                
                try:
                    post_save.disconnect(notification_handler, sender=Notification)
                    notification = Notification.objects.create(
                        user_id=request.user,
                        where_to="task",
                        notification_msg=f"You have been assigned new task: {task.task_topic}",
                        action_content_type=ContentType.objects.get_for_model(Tasks),
                        action_id=task.id
                    )
                    
                    notification.notification_to.set(assign_users)
                    post_save.connect(notification_handler, sender=Notification)
                    post_save.send(sender=Notification, instance=notification, created=True)
                    # Redirect_to.objects.create(notification=notification, link="/employee/meeting")
                    
                except Exception as e:
                    print("Notification creation failed:", e)

                        

                serializer.save()

                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Task created successfully.",
                    "data": {
                        "task": serializer.data,
                        "attachments": [attachment.attachment for attachment in task_attachments]
                    }
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create Task.",
                    "errors": serializer.errors
                })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error.",
                "errors": str(e)
            })
        
    @csrf_exempt
    def get_unassigned_users_task(self, request):
        try:
            task_id = request.GET.get('task_id')
            user_id = request.GET.get('user_id')

            if not task_id or not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. Both task_id and user_id are required."
                })

            task = Tasks.objects.filter(id=task_id).first()
            if not task:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task not found."
                })

            user = User.objects.filter(id=user_id).first()
            if not user:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "User not found."
                })

            employee_details = EmployeePersonalDetails.objects.get(user_id=user_id)
            # unassigned_users = User.objects.exclude(assign_to_task__id=task_id)
            # unassigned_users = User.objects.filter(user_role="Dev::Employee",verified=1).exclude(assign_to_task__id=task_id)
            unassigned_users = User.objects.filter(employeepersonaldetails__organization_id=employee_details.organization_id,employeepersonaldetails__organization_location=employee_details.organization_location, verified=1,user_role="Dev::Employee",active=True).exclude(assign_to_task__id=task_id)

            
            unassigned_users = unassigned_users.exclude(id=user_id)

            
            user_serializer = UserSerializer(unassigned_users, many=True)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Unassigned users retrieved successfully.",
                "data": user_serializer.data
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve unassigned users.",
                "errors": str(e)
            })

    @csrf_exempt
    def create_task_individual(self, request):
        print(request.data)
        serializer = TaskIndividualSerializer(data=request.data)

        try:
            if serializer.is_valid():
                task = serializer.save()
                # assign_user_ids = request.data['assign_to']
                assign_user_ids = request.data.get('assign_to', [])
                assign_users = User.objects.filter(id__in=assign_user_ids)
                task.assign_to.set(assign_users)

                attachments = request.FILES.getlist('attachments') 
                print("-----------------")
                print(attachments)
                task_attachments = []
                for attachment in attachments:
                    try:
                        
                        file_name = ''.join(random.choices('0123456789', k=8)) + '_' + attachment.name
                        file_path = '/employee/task_attachment/' + file_name
                        fs = FileSystemStorage()
                        fs.save(file_path, attachment)

                       
                        task_attachment = TaskAttachments.objects.create(task=task, attachment=file_path)
                        task_attachments.append(task_attachment)
                    except Exception as e:
                        pass
                  
                        

                serializer.save()

                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Task created successfully.",
                    "data": {
                        "task": serializer.data,
                        "attachments": [attachment.attachment for attachment in task_attachments]
                    }
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create Task.",
                    "errors": serializer.errors
                })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error.",
                "errors": str(e)
            })
    
    @csrf_exempt
    def UpdateTaskAssignTo(self, request):
        try:
            task_id = request.data.get('task_id')
            user_id = request.data.get('user_id')

            if not task_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id is missing.",
                })

            try:
                task = Tasks.objects.get(id=task_id)
            except Tasks.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task not found",
                })

            assign_user_ids_str = request.data.get('assign_to', '')
            print(assign_user_ids_str)

            try:
                assign_user_ids = [int(user_id) for user_id in assign_user_ids_str.split(',') if user_id.strip()]
            except ValueError:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid user IDs format",
                })

            assign_users = User.objects.filter(id__in=assign_user_ids)
            
            user_intance = User.objects.get(id=user_id)
            
            try:    
                post_save.disconnect(notification_handler, sender=Notification)
                
                # Get currently assigned users
                current_assigned_users = set(task.assign_to.all())

                # Determine new users to notify
                new_users_to_notify = [user for user in assign_users if user not in current_assigned_users]

                notification = Notification.objects.create(
                    user_id=user_intance,
                    where_to="customboard" if task.checklist else "myboard",
                    notification_msg=f"You have been assigned a Task: {task.task_topic}",
                    action_content_type=ContentType.objects.get_for_model(Tasks),
                    action_id=task.id,
                    other_id =task.checklist.board.id if task.checklist else None,
                    
                )
                

                notification.notification_to.set(new_users_to_notify)
                    
                    
                post_save.connect(notification_handler, sender=Notification)
                post_save.send(sender=Notification, instance=notification, created=True)
                task.assign_to.set(assign_users)
            except Exception as e:
                print("-------------error",str(e))
                pass
            
            
            
            task.assign_to.set(assign_users)
            task.save()

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task updated successfully",
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update Task",
                "errors": str(e),
            })



    # @csrf_exempt
    # def UpdateTaskAssignTo(self, request):
    #     try:    
    #         task_id = request.data.get('task_id')
    #         task = Tasks.objects.get(id=task_id)
    #         if task_id:


    #             try:
    #                 assign_user_ids_str = request.data.get('assign_to', '')
    #                 print(assign_user_ids_str)
    #                 assign_user_ids = [int(user_id) for user_id in assign_user_ids_str.split(',') if user_id.strip()] 
    #                 assign_users = User.objects.filter(id__in=assign_user_ids)
    #                 print("-------------------heyyyyy")
    #                 existing_assignees = task.assign_to.values_list('id', flat=True)
    #                 new_assignees = [user_id for user_id in assign_user_ids if user_id not in existing_assignees]
    #                 print(new_assignees)
                    
    #                 task.assign_to.add(*assign_users)
    #                 task.save()

    #             except Tasks.DoesNotExist:
    #                 return JsonResponse({
    #                     "success": False,
    #                     "status": status.HTTP_404_NOT_FOUND,
    #                     "message": "Task not found",
    #                 })

    #         return JsonResponse({
    #             "success": True,
    #             "status": status.HTTP_200_OK,
    #             "message": "Task updated successfully",
               
    #         })
    #     except Tasks.DoesNotExist:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_404_NOT_FOUND,
    #             "message": "Task not found",
    #         })
    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "Failed to update Task",
    #             "errors": str(e)
    #         })


    @csrf_exempt
    def updateTaskData(self, request):
        task_id = request.data.get('task_id')
        try:
            task = Tasks.objects.get(id=task_id)
        except Tasks.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "task not found",
            })

        serializer = TaskSerializer(task, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task updated successfully",
                "data": serializer.data
            })
        return JsonResponse({
            "success": False,
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid data",
            "errors": serializer.errors
        })






    @csrf_exempt
    def changeIndividualTaskStatus(self, request):
        try:
            
            task_id = request.data.get('task_id')
            Status = request.data.get('status')
            user_id = request.data.get('user_id')

            
            if not task_id or not Status or not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id or status or user_id is missing."
                })
            
            closed_status_ids = get_status_ids_from_creater_side(user_id )
                
            try:
                
                got_task_statu = TaskStatus.objects.get(id=Status)
                
                if got_task_statu.id in closed_status_ids:
                   
                    tasks = Tasks.objects.filter(Q(~Q(created_by=user_id)) & Q(assign_to=user_id), id=task_id).distinct().first()
                    print(tasks)
                    tasks_oob = Tasks.objects.filter(Q(~Q(created_by=user_id)) & Q(~Q(assign_to=user_id)), id=task_id).distinct().first()
                    if tasks:
                        return JsonResponse({
                            "success": True,
                            "status": 124,
                            "message": "Permission denied: Unable to change the task status to Done."
                        })
                    elif tasks_oob:
                        return JsonResponse({
                            "success": True,
                            "status": 124,
                            "message": "Permission denied."
                        })
                    else:
                        pass
                
                task = Tasks.objects.filter(Q(created_by=user_id) | Q(assign_to=user_id), id=task_id).distinct().first()
                
           
                
                
                if task == None:
                    return JsonResponse({
                        "success": True,
                        "status": 124,
                        "message": "Permission denied: Unable to change the task status."
                    })

                
                
            except Tasks.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": 403,
                    "message": "You don't have permission to update this task",
                })
            
            
      
            int_status = int(Status)
            task = Tasks.objects.get(id=task_id)
                
            before_task_updated_status = task.status
            

            opened_status_ids = get_status_ids_from_assigned_side(user_id)
            opened_status_ids_with_complete = get_status_ids_from_assigned_side(user_id, True)

            
            if before_task_updated_status.id in opened_status_ids and int_status not in opened_status_ids:
                to_close_task_checklist = TaskChecklist.objects.filter(Task=task, inTrash= False).distinct().count()
                

                to_close_task_checklist_with_status = len(TaskChecklist.objects.filter(Task=task,completed=True, inTrash= False).distinct())
                if to_close_task_checklist != to_close_task_checklist_with_status:
                    response = {"success": True, 
                                "status": 123, 
                                "message": "Unable to update task status: Sub-checklist is incomplete."}

                    return JsonResponse(response)
                else:
                    to_close_task_subtask = SubTasks.objects.filter(Task=task, inTrash= False).distinct().count()
                

                    to_close_task_subtask_with_status = len(SubTasks.objects.filter(Task=task,status__in=opened_status_ids_with_complete, inTrash= False).distinct())
                    
            
                    
                    if to_close_task_subtask != to_close_task_subtask_with_status:
                        
                    
                        response = {
                            "success": True,
                            "status": 123,
                            "message": "Unable to update task status: The status of one or more sub-tasks differs from the main task."
                        }


                        return JsonResponse(response)
                    
    
   
            
            # ----------------
            user__id=User.objects.get(id=user_id)
            if before_task_updated_status.id in closed_status_ids:
                if got_task_statu.id not in closed_status_ids:
                    task.reopened_count+=1
                    
                    TaskAction.objects.create(
                        user_id=user__id,
                        task=task,
                        remark=f"Task has been reopened {before_task_updated_status.status_name} to {got_task_statu.status_name}",
                    )
            else:
                if before_task_updated_status.id == got_task_statu.id:
                    pass
                else:
                    print(task)
                    TaskAction.objects.create(
                                user_id=user__id,
                                task=task,
                                remark=f"Task status has been updated {before_task_updated_status.status_name} to {got_task_statu.status_name}",
                            )
  
            
            
            task.status = got_task_statu
            
            task.save()
            
            try:    
                post_save.disconnect(notification_handler, sender=Notification)
                notification = Notification.objects.create(
                    user_id=request.user,
                    where_to="customboard" if task.checklist else "myboard",
                    notification_msg=f"Task '{task.task_topic}' Status has been updated to {got_task_statu.status_name}",
                    action_content_type=ContentType.objects.get_for_model(Tasks),
                    action_id=task.id
                )
                
  
                if str(user_id) == str(task.created_by.id):                    
                    notification.notification_to.set(task.assign_to.all())
                else:
                    notification.notification_to.add(task.created_by)
                    
                    # Exclude user_id from task.assign_to.all() if user_id is present in assign_to
                    assigned_users = task.assign_to.exclude(id=user_id).all()
                    notification.notification_to.add(*assigned_users)
                    
                post_save.connect(notification_handler, sender=Notification)
                post_save.send(sender=Notification, instance=notification, created=True)
            except Exception as e:
                pass
            


            # serializer = TaskSerializer(task)
            # handle this also task_checklist==task_checklist_with_status here only because of from manage like that
            response={
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task status updated successfully.",
            }

            return JsonResponse(response)

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
                "message": "Failed to update task status.",
                "errors": str(e)
            })

  

    @csrf_exempt
    def updateUserTasks(self, request):
        try:
            task_id = request.data.get('task_id')
            user_id = request.data.get('user_id')

            if not (task_id and user_id):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id and user_id are required."
                })

            task = Tasks.objects.get(id=task_id)

            
            due_date = request.data.get('due_date')
            if due_date is not None:

                task.due_date = due_date

                
                user__id=User.objects.get(id=user_id) 
                notification = TaskAction.objects.create(
                    user_id=user__id, 
                    task=task,
                    remark=f"Task Due Date has been updated", )

            
            urgent_status = request.data.get('urgent_status')
            if urgent_status is not None:
                task.urgent_status = urgent_status
            
            desc = request.data.get('task_description')
            if desc is not None:
                task.task_description = desc
            
            topic = request.data.get('task_topic')
            if topic is not None:
                task.task_topic = topic

            
            assign_to = request.data.get('assign_to')
            if assign_to is not None:
                assign_users = User.objects.filter(id__in=assign_to)
                task.assign_to.set(assign_users)

            task.save()

            serializer = TaskGetSerializer(task)

            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task updated successfully.",
                "data": serializer.data
            }

            return compress(response)

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
                "message": "Failed to update task.",
                "errors": str(e)
            })



    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('task_id', openapi.IN_QUERY, description="task_id ID parameter", type=openapi.TYPE_INTEGER,default=1)
    ]) 
    @csrf_exempt
    def deleteTaskData(self, request):
        task_id = request.GET.get('task_id')
        user_id = request.GET.get('user_id')
        print(task_id)
        try:
            task = Tasks.objects.get(id=task_id,created_by_id=user_id)
        except Tasks.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Tasks not found",
            })
        print(task)
        task.inTrash=True
        task.save()
        
        TaskChecklist.objects.filter(Task = task.id).update(inTrash=True,trashed_with="Relatively_task")
        # SubTasks.objects.filter(task_checklist__Task=task.id).update(inTrash=True, trashed_with="Relatively_task")
        # task.delete()
        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "Tasks Trashed successfully",
        })  
    

    @csrf_exempt
    def getTaskData(self, request):
        try:
            task = Tasks.objects.all()
            serializer = TaskSerializer(task, many=True)
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task retrieved successfully",
                "data": serializer.data
            })
        except TemplateChecklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Task Attachment not found."
            })
    
    
    
    def get_task_set_by_status_name(self,user_id):
        get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)
        task_statuses = TaskStatus.objects.filter(organization=get_org_id.organization_id).order_by('order')
        return task_statuses


   

    @csrf_exempt
    def getUserTasks(self, request):
        # try:
            user_id = request.GET.get('user_id')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id is missing."
                })

            
            current_time = datetime.now()
            due_date_end = current_time + newTimezone.timedelta(hours=24)
            
            # due_date_end_str = due_date_end.strftime('%Y-%m-%dT%H:%M')
            # due_date_end_str = due_date_end.strftime('%Y-%m-%dT%H:%M:%S%z')
            
            opened_status_ids = get_status_ids_from_assigned_side(user_id)
            # fixed_state_mapping = {
            #     "Pending": "Pending",
            #     "InProgress": "InProgress"
            # }  
               
            # fixed_states_to_include = fixed_state_mapping.values()
            # get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)

            # task_statuses = TaskStatus.objects.filter(fixed_state__in=fixed_states_to_include,organization=get_org_id.organization_id).order_by('order')

            # # Get the corresponding fixed_state IDs
            # fixed_state_ids = [status.id for status in task_statuses]

            # Task
            urjent_tasks = Tasks.objects.filter(
                Q(urgent_status=True, status__id__in=opened_status_ids),
                Q(due_date__gt=current_time),
                Q(created_by=user_id) | Q(assign_to=user_id),
                status__isnull=False, 
                is_personal=False,
                inTrash=False
            ).order_by('due_date')
            

            overdue_tasks = Tasks.objects.filter(
                Q(status__id__in=opened_status_ids),
                Q(due_date__lte=current_time) ,
                Q(created_by=user_id) | Q(assign_to=user_id),
                status__isnull=False,
                is_personal=False,
                inTrash=False
                
            ).order_by('due_date')
            
       
        
            about_to_end = Tasks.objects.filter(
                Q(status__id__in=opened_status_ids),
                Q(due_date__gt=current_time, due_date__lte=due_date_end),
                Q(created_by=user_id) | Q(assign_to=user_id),
                status__isnull=False,
                is_personal=False,
                inTrash=False
                
            ).order_by('due_date')
            
            
            # Sub Task
            sub_task = SubTasks.objects.filter(
                Q(status__id__in=opened_status_ids),
                Q(due_date__gt=current_time, due_date__lte=due_date_end),
                Q(created_by=user_id) | Q(assign_to=user_id),
                status__isnull=False,
                inTrash=False
                
            ).order_by('due_date')
            
            
            overdue_sub_tasks = SubTasks.objects.filter(
                Q(status__id__in=opened_status_ids),
                Q(due_date__lte=current_time) ,
                Q(created_by=user_id) | Q(assign_to=user_id),
                status__isnull=False,
                inTrash=False
                
            ).order_by('due_date')
            
            # Sub Task child
            sub_task_child = SubTaskChild.objects.filter(
                Q(status__id__in=opened_status_ids),
                Q(due_date__gt=current_time, due_date__lte=due_date_end),
                Q(created_by=user_id) | Q(assign_to=user_id),
                status__isnull=False,
                inTrash=False
                
            ).order_by('due_date')

            overdue_sub_tasks_child = SubTaskChild.objects.filter(
                Q(status__id__in=opened_status_ids),
                Q(due_date__lte=current_time) ,
                Q(created_by=user_id) | Q(assign_to=user_id),
                status__isnull=False,
                inTrash=False
                
            ).order_by('due_date')

            
            # personal Board
            
            # Mapping for fixed states
            fixed_state_mapping = {
                "Pending": "Pending",
                "InProgress": "InProgress"
            }

            # Values to include in the query
            personal_fixed_states_to_include = fixed_state_mapping.values()

            # Get the organization ID associated with the user

            # Get the corresponding fixed_state IDs directly using values_list
            fixed_state__personal_ids = list(PersonalStatus.objects.filter(
                fixed_state__in=personal_fixed_states_to_include, 
                user_id=user_id
            ).order_by('order').values_list('id', flat=True))

            
            personal_board = PersonalTask.objects.filter(
                Q(status__id__in=fixed_state__personal_ids),
                Q(due_date__gt=current_time, due_date__lte=due_date_end),
                Q(user_id=user_id ),
                status__isnull=False,
                inTrash=False
                
            ).order_by('due_date')
            
            
            overdue_personal_tasks = PersonalTask.objects.filter(
                Q(status__id__in=fixed_state__personal_ids),
                Q(due_date__lte=current_time) ,
                Q(user_id=user_id ),
                status__isnull=False,
                inTrash=False
                
            ).order_by('due_date')
            
  
            all_pending_tasks = urjent_tasks | overdue_tasks | about_to_end
            
            all_pending_subTask = sub_task | overdue_sub_tasks
            
            all_pending_subTaskChild = sub_task_child | overdue_sub_tasks_child
            


            serializer = TaskGetSerializer(all_pending_tasks, many=True)
            
            sub_task_serializer = SubTaskGetSerializer(all_pending_subTask, many=True)
            
            sub_task_child_serializer = SubTaskChildGetSerializer(all_pending_subTaskChild, many=True)

            # all_pending_data = serializer.data
            all_pending_personal_Task = personal_board | overdue_personal_tasks
    
            personal_task_serializer = GetPersonalTaskOnMyDaySerializer(all_pending_personal_Task, many=True)
        
            task_ids_set = set()
            unique_tasks = []
            combined_tasks = serializer.data + sub_task_serializer.data + sub_task_child_serializer.data +personal_task_serializer.data
            for task in combined_tasks:
                task_id = task["id"]
                if task_id not in task_ids_set:
                    task_ids_set.add(task_id)
                    unique_tasks.append(task)
                    
                    

            
            urgent_tasks_set = set(Tasks.objects.filter(urgent_status=True, status__id__in=opened_status_ids, created_by=user_id,status__isnull=False,is_personal=False,inTrash=False, due_date__isnull=False) | Tasks.objects.filter(urgent_status=True, status__id__in=opened_status_ids, status__isnull=False,assign_to=user_id,is_personal=False, inTrash=False, due_date__isnull=False).values_list('id', flat=True))
            reopened_tasks_set = set(Tasks.objects.filter(created_by=user_id,inTrash=False,status__isnull=False, is_personal=False, reopened_count__gt=0) | Tasks.objects.filter( assign_to=user_id, inTrash=False,status__isnull=False,is_personal=False, reopened_count__gt=0).values_list('id', flat=True))

            total_count = Tasks.objects.filter(Q(created_by=user_id) | Q(assign_to=user_id),inTrash=False,status__isnull=False, is_personal=False,due_date__isnull=False).distinct().count()
            status_lengths = {"Total": {"count": total_count, "avg": 100},
                              "Urgent": {"count": len(urgent_tasks_set), "avg": round((len(urgent_tasks_set) / total_count) * 100, 2) if total_count > 0 else 0},
                              "Reopened": {"count": len(reopened_tasks_set), "avg": round((len(reopened_tasks_set) / total_count) * 100, 2) if total_count > 0 else 0}
                              }
            status_lengths_urgent={}
            for Status in self.get_task_set_by_status_name(user_id):
                task_set = set(
                    Tasks.objects.filter(status=Status, created_by=user_id, inTrash=False, is_personal=False,status__isnull=False,due_date__isnull=False) |
                    Tasks.objects.filter(status=Status, assign_to=user_id, inTrash=False, status__isnull=False,due_date__isnull=False).values_list('id', flat=True)
                )
                
                length = len(task_set)
                average = round((length / total_count) * 100, 2) if total_count > 0 else 0
                
                status_lengths[Status.status_name] = {"count": length, "avg": average}
                
                
                # For Urgent task counts
                urgent_task_set = set(
                    Tasks.objects.filter(urgent_status=True, status=Status, created_by=user_id,is_personal=False,inTrash=False,status__isnull=False, due_date__isnull=False) | 
                    Tasks.objects.filter(urgent_status=True, status=Status, assign_to=user_id, inTrash=False,is_personal=False,status__isnull=False, due_date__isnull=False).values_list('id', flat=True)
                )
                
                length = len(urgent_task_set)
                
                
                status_lengths_urgent[Status.status_name] = {"count": length}
                
                
        
            total_count = Tasks.objects.filter(Q(created_by=user_id) | Q(assign_to=user_id),inTrash=False, is_personal=False,status__isnull=False, due_date__isnull=False).distinct().count()
    
            status_counts_list = [
                {"status": "Total", "count": status_lengths["Total"]["count"], "avg": status_lengths["Total"]["avg"]},
                {"status": "Urgent", "count": status_lengths["Urgent"]["count"], "avg": status_lengths["Urgent"]["avg"]},
                {"status": "Reopened", "count": status_lengths["Reopened"]["count"], "avg": status_lengths["Reopened"]["avg"]},
            ] + [
                {"status": status.status_name, "count": status_lengths[status.status_name]["count"], "avg": status_lengths[status.status_name]["avg"]} for status in self.get_task_set_by_status_name(user_id)
            ]
            
            
            status_urgent_list = [{"status": status.status_name, "count": status_lengths_urgent[status.status_name]["count"]} for status in self.get_task_set_by_status_name(user_id)]

            response_data = {
                "tasks": unique_tasks,
                "counts": {
                    "status_counts":status_counts_list,
                    "urgent_counts":status_urgent_list
                },

            }

            for task in response_data["tasks"]:
                checklist_id = task.get("checklist")
                if checklist_id:
                    try:
                        checklist = Checklist.objects.get(id=checklist_id)
                        task["board_id"] = checklist.board_id
                    except Checklist.DoesNotExist:
                        pass

            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "User tasks retrieved successfully.",
                "data": response_data
            }

            return compress(response)

        # except Exception as e:
        #     print("Error")
        #     print(e)
        #     return JsonResponse({
        #         "success": False,
        #         "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         "message": "Failed to retrieve user tasks.",
        #         "errors": str(e)
        #     })






    def serialize_status_info(self, status_info):
        return {
            "id": status_info["id"],
            "status_name": status_info["status_name"],
            "color": status_info["color"],
        }

        
    @csrf_exempt
    def getUserTask_NotCheck(self, request):

      
        user_id = request.GET.get('user_id')

        if not user_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. user_id is missing."
            })
        userr = User.objects.get(id=user_id)

        tasks_created_by = Tasks.objects.filter(
            created_by=user_id, checklist=None,is_personal=False,inTrash=False).order_by('due_date')
        tasks_assigned_to = Tasks.objects.filter(
            assign_to=user_id, checklist=None,is_personal=False, inTrash=False).order_by('due_date')

        assigned_checklist_tasks = SubTasks.objects.filter(
            assign_to=user_id, due_date__isnull =False, inTrash=False).values_list('Task', flat=True).distinct()
        
        assigned_subtask_child = SubTaskChild.objects.filter(
            assign_to=user_id, due_date__isnull =False, inTrash=False).values_list('subtasks__Task', flat=True).distinct()
        
        print(assigned_subtask_child)
        parent_tasks = Tasks.objects.filter(
            id__in=assigned_checklist_tasks, inTrash=False).order_by('due_date')
        
        parent_tasks_child = Tasks.objects.filter(
            id__in=assigned_subtask_child, inTrash=False).order_by('due_date')
        

        all_tasks = set()

        # Add task IDs to the set
        for task in tasks_created_by:
            all_tasks.add(f"t_{task.id}")
        for task in tasks_assigned_to:
            all_tasks.add(f"t_{task.id}")
        for parent_task in parent_tasks:
            all_tasks.add(f"t_{parent_task.id}")
        
        for parent_task_sub_child in parent_tasks_child:
            all_tasks.add(f"t_{parent_task_sub_child.id}")
            
        get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)
        task_statuses = TaskStatus.objects.filter(organization=get_org_id.organization_id).order_by('order', 'created_at')

        fixed_state_titles_and_ids = [(Status.status_name,Status.fixed_state,Status.order ,Status.id) for Status in task_statuses]

        data = [
            {"id": f"s_{status_id}", "title": title,"fixed_state":fix_state,"order": order, "status_id": status_id, "tasks": []}
            for idx, (title,fix_state, order ,status_id) in enumerate(fixed_state_titles_and_ids)
        ]


  
        
        
        closed_status_ids = get_status_ids_from_creater_side(user_id, True)
        

        for task_id in all_tasks:
            task_num = int(task_id.split("_")[1])
            task = Tasks.objects.get(id=task_num)
            
            
            Checklisttask = SubTasks.objects.filter(Task=task, inTrash= False, due_date__isnull = False)
            total_duration_to_due_date = timedelta()  # Initialize total duration
            for checklist_task in Checklisttask: 
                # Calculate duration to due date
                
                due_date = checklist_task.due_date
                if due_date:
                    now = newTimezone.localtime(newTimezone.now())
                    duration_to_due_date = due_date - now
 
                    total_duration_to_due_date += duration_to_due_date
                  
            
            total_days = total_duration_to_due_date.days
            total_hours = total_duration_to_due_date.seconds // 3600  # Convert seconds to hours

            # Calculate the total duration in the format "X days, Y hours"

            total_checklist_task = Checklisttask.count()

            
            # completed_checklist_task = Checklisttask.filter(status__id__in=fixed_state_id).count()
            completed_checklist_task = Checklisttask.filter(status__id__in=closed_status_ids)
            # Initialize total duration of completed checklist tasks
            total_duration_completed = timedelta()
            
            # Calculate the total duration of completed checklist tasks
            for checklist_task in completed_checklist_task:
                due_date = checklist_task.due_date
                if due_date:
                    now = newTimezone.localtime(newTimezone.now())
                    duration_to_due_date = due_date - now
                    total_duration_completed += duration_to_due_date
            
            
            progress_percentage = 100
     
            if total_duration_to_due_date.total_seconds() > 0:
                
                if task.status and task.status.id in closed_status_ids:
                    pass
                else:
                    # progress_percentage = round((completed_checklist_task / total_checklist_task) * 100 ,2)
                    progress_percentage = round((total_duration_completed.total_seconds() / total_duration_to_due_date.total_seconds()) * 100, 2)                    
            elif task.status and task.status.id in closed_status_ids:
                
                progress_percentage =  100
            
            else:
                progress_percentage =  0
                
            
            created_by_data = serialize('json', [task.created_by])
            created_by_data = created_by_data[1:-1]
            created_by_data = {
                "id": task.created_by.id,
                "email": task.created_by.email,
                "firstname": task.created_by.firstname,
                "lastname": task.created_by.lastname,
            }
            
            # print("----------------------ala")
            # print(task_id,task.task_topic )

            if task.due_date:
                IST = pytz.timezone('Asia/Kolkata')
                
                due_date_ist = task.due_date.astimezone(IST)
                
                task_data = {
                    "id": task_id,
                    "title": task.task_topic,
                    "description": task.task_description,
                    "due_date": due_date_ist.strftime('%Y-%m-%d %H:%M:%S%z'),
                    "urgent_status": task.urgent_status,
                    "status": task.status,
                    "reopened_count":task.reopened_count,
                    "created_at": task.created_at.isoformat(),
                    "created_by": created_by_data,
                    "progress_percentage": max(progress_percentage, 0) ,
                    "division": f"{completed_checklist_task.count()}/{total_checklist_task}",
                    
                }
            else:
                task_data = {
                    "id": task_id,
                    "title": task.task_topic,
                    "description": task.task_description,
                    "due_date": None,
                    "urgent_status": task.urgent_status,
                    "status": task.status,
                    "reopened_count":task.reopened_count,
                    "created_at": task.created_at.isoformat(),
                    "created_by": created_by_data,
                    "progress_percentage": max(progress_percentage, 0),
                    "division": f"{completed_checklist_task.count()}/{total_checklist_task}",
                    
                }
            
            # print("-------------------aheree")
            for idx, (title,fix_state, order,status_id) in enumerate(fixed_state_titles_and_ids):
                if task.status and task.status.id == status_id:
                    status_info = {
                        "id": task.status.id,
                        "status_name": task.status.status_name,
                        "color": task.status.color,
                    }
                    task_data["status"] = status_info
                    data[idx]["tasks"].append(task_data)
                    break

        for section in data:
            section["tasks"] = [task for task in section["tasks"] if task.get("due_date")]
            section["tasks"] = sorted(section["tasks"], key=lambda task: task.get("due_date"))
            
            # section["tasks"] = sorted(section["tasks"], key=lambda task: task.get("due_date").isoformat() if task.get("due_date") else "")

        
        try:
            board_view = UserFilters.objects.get(user=user_id).myboard_view
        except Exception as e:
            board_view = None
        
        users_with_access_gave = TaskSpecialAccess.objects.filter(user=userr).select_related('access_to')
        
        access_list_gave = [
            {
                'user_id': access.access_to.id,
                'user_email': access.access_to.email,
                'access_type': access.access_type
            } for access in users_with_access_gave
        ]
        
        response = {
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "User tasks retrieved successfully.",
            "access_to": access_list_gave,
            "data": data,
            "board_view":board_view
        }

        return JsonResponse(response, encoder=DateTimeEncoder)

      


    @csrf_exempt
    def get_task_assigned_users(self,request):
        try:
            
            task_id = request.GET.get('task_id')
            task = get_object_or_404(Tasks, id=task_id)


            assigned_users = task.assign_to.all()

            serializer = UserSerializer(assigned_users, many=True)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Tasks in retrieved successfully.",
                "data": serializer.data
            })

        except Tasks.DoesNotExist:
            return JsonResponse({
                "success": True,
                "error": "Task not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve Tasks.",
                "errors": str(e)
            })

    @csrf_exempt
    def update_task_checklist(self, request):
        print(request.data)
        try:
            user_id = request.data.get('user_id')
            task_id = request.data.get('task_id')
            checklist_id = request.data.get('checklist_id')
            sequence = request.data.get('sequence')  

            if not (user_id and task_id and checklist_id):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id, task_id, and checklist_id are required."
                })

            task = Tasks.objects.get(id=task_id)

            # if user_id not in [str(task.created_by.id)] + list(task.assign_to.values_list('id', flat=True)):
            #     return JsonResponse({
            #         "success": False,
            #         "status": status.HTTP_403_FORBIDDEN,
            #         "message": "User is not authorized to update the task's checklist."
            #     })

            checklist = Checklist.objects.get(id=checklist_id)
            
            if sequence is not None:
                try:
                    sequence = float(sequence)
                except ValueError:
                    sequence = None

                if sequence is not None and sequence <= 0.000005:
                    # Update the sequences of tasks in the checklist with consecutive values starting from 5
                    checklist_tasks = Tasks.objects.filter(checklist=checklist).order_by('sequence')
                    new_sequence = 5.0
                    for task_in_checklist in checklist_tasks:
                        task_in_checklist.sequence = new_sequence
                        task_in_checklist.save()
                        new_sequence += 1.0
                else:
                    # Update the sequence of the task
                    task.sequence = sequence
                    task.save()

            task.checklist = checklist
            task.save()

            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task's checklist updated successfully.",
                "data": {
                    "task_id": task_id,
                    "checklist_id": checklist_id
                }
            }

            return JsonResponse(response)

        except Tasks.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Task not found.",
            })
        except Checklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Checklist not found.",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update task's checklist.",
                "errors": str(e)
            })


    # @csrf_exempt
    # def update_task_checklist(self, request):
    #     print(request.data)
    #     try:
    #         user_id = request.data.get('user_id')
    #         task_id = request.data.get('task_id')
    #         checklist_id = request.data.get('checklist_id')

    #         if not (user_id and task_id and checklist_id):
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": status.HTTP_400_BAD_REQUEST,
    #                 "message": "Invalid request. user_id, task_id, and checklist_id are required."
    #             })

    #         task = Tasks.objects.get(id=task_id)

            
    #         if user_id not in [str(task.created_by.id)] + list(task.assign_to.values_list('id', flat=True)):
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": status.HTTP_403_FORBIDDEN,
    #                 "message": "User is not authorized to update the task's checklist."
    #             })

    #         checklist = Checklist.objects.get(id=checklist_id)
    #         task.checklist = checklist
    #         task.save()

    #         response = {
    #             "success": True,
    #             "status": status.HTTP_200_OK,
    #             "message": "Task's checklist updated successfully.",
    #             "data": {
    #                 "task_id": task_id,
    #                 "checklist_id": checklist_id
    #             }
    #         }

    #         return compress(response)

    #     except Tasks.DoesNotExist:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_404_NOT_FOUND,
    #             "message": "Task not found.",
    #         })
    #     except Checklist.DoesNotExist:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_404_NOT_FOUND,
    #             "message": "Checklist not found.",
    #         })
    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "Failed to update task's checklist.",
    #             "errors": str(e)
    #         })

    def get_task_actions_and_chats(self,request):
        try:
            task_id = request.GET.get('task_id')

            if not task_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id is missing."
                })

            

            task_actions = TaskAction.objects.filter(task_id=task_id).select_related('user_id').values(
            'task_id', 'created_at'
        ).annotate(username=Concat('user_id__firstname', Value(' '), 'user_id__lastname'), sender_id=F('user_id'),message=F('remark'))

            task_chats = TaskChatting.objects.filter(task_id=task_id).values('task_id', 'sender_id', 'message', 'created_at').annotate(username=Concat('sender_id__firstname', Value(' '), 'sender_id__lastname'))

            merged_data = sorted(chain(task_actions, task_chats), key=lambda x: x['created_at'])
            
            
            for item in merged_data:
                if item.get('message') and 'chat_files' in item['message']:
                  
                    file_path=settings.MEDIA_ROOT+"/"+item.get('message')
                    # print(file_path)

                    # Get the file size
                    try:
                        size = os.path.getsize(file_path)
                        # Convert size to human-readable format
                        size_kb = size / 1024
                        size_str = f"{size_kb:.2f} KB" if size_kb < 1024 else f"{size_kb / 1024:.2f} MB"
                        item['file_size'] = size_str
                    except Exception as e:
                       
                        # Handle error if unable to get file size
                        item['file_size'] = 'Unknown'
                else:
                    item['file_size'] = -1 

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task actions and chats retrieved successfully.",
                "data": merged_data
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve task actions and chats.",
                "errors": str(e)
            })

    # def get_task_actions_and_chats(self,request):
    #     try:
    #         task_id = request.GET.get('task_id')

    #         if not task_id:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": status.HTTP_400_BAD_REQUEST,
    #                 "message": "Invalid request. task_id is missing."
    #             })

            
    #         task_actions = TaskAction.objects.filter(task_id=task_id)
    #         task_chats = TaskChatting.objects.filter(task_id=task_id)

            
    #         merged_data = sorted(chain(task_actions, task_chats), key=lambda x: x.created_at)

            
    #         class TaskActionChattingSerializer(serializers.Serializer):
    #             user_id = serializers.PrimaryKeyRelatedField(read_only=True)
    #             task = serializers.PrimaryKeyRelatedField(read_only=True)
    #             remark = serializers.CharField(read_only=True)
    #             message = serializers.CharField(read_only=True)
    #             created_at = serializers.DateTimeField(read_only=True)

            
    #         merged_serializer = TaskActionChattingSerializer(merged_data, many=True)

    #         return JsonResponse({
    #             "success": True,
    #             "status": status.HTTP_200_OK,
    #             "message": "Task actions and chats retrieved successfully.",
    #             "data": merged_serializer.data
    #         })

    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "Failed to retrieve task actions and chats.",
    #             "errors": str(e)
    #         })

    
    @csrf_exempt
    def getUserSpecificTasks(self, request):
        try:
            user_id = request.GET.get('user_id')
            Status = request.GET.get('status')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id is missing."
                })
            
            fixed_state_mapping = {
                "Pending": "Pending",
                "InProgress": "InProgress"
            }
            
            fixed_states_to_include = fixed_state_mapping.values()
            get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)

            task_statuses = TaskStatus.objects.filter(fixed_state__in=fixed_states_to_include,organization=get_org_id.organization_id).order_by('order')

            fixed_state_ids = [Status.id for Status in task_statuses]
            
            if Status == "Urgent":
                filtered_tasks = TaskHierarchy.objects.filter(
                    Q(inTrash=False),
                    Q(urgent_status=True, status__id__in=fixed_state_ids),
                    Q(created_by=user_id) | Q(assign_to=user_id),
                    status__isnull=False,
                    is_personal=False
                    
                ).distinct().order_by('due_date')
            elif Status == "Total":
                filtered_tasks = TaskHierarchy.objects.filter(
                    Q(due_date__isnull=False),
                    Q(inTrash=False),
                    Q(created_by=user_id) | Q(assign_to=user_id),
                    status__isnull=False,
                    is_personal=False
                    
                ).distinct().order_by('due_date')
            elif Status == "Reopened":
                filtered_tasks = TaskHierarchy.objects.filter(
                    Q(inTrash=False),
                    Q(created_by=user_id) | Q(assign_to=user_id),
                    reopened_count__gt=0,
                    status__isnull=False,
                    is_personal=False
                    
                ).distinct().order_by('due_date')
            else:
                task_status = TaskStatus.objects.get(status_name=Status,organization=get_org_id.organization_id)
                filtered_tasks = TaskHierarchy.objects.filter(
                    Q(due_date__isnull=False),
                    Q(inTrash=False),
                    Q(status=task_status),
                    Q(created_by=user_id) | Q(assign_to=user_id),
                    # status__isnull=False,
                    is_personal=False
                    
                ).distinct().order_by('due_date')


            serializer = HierarchyTaskGetSerializer(filtered_tasks, many=True)       

            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "User tasks retrieved successfully.",
                "data": serializer.data
            }

            return compress(response)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve user tasks.",
                "errors": str(e)
            })
    
   
    


class ChangeTaskStatusViewSet(viewsets.ModelViewSet):
    def changeStatus(self,request):
        tasks_to_update = Tasks.objects.filter(status="Completed")
        tasks_to_update.update(status="InReview")
        return JsonResponse({"message": "Tasks updated successfully."}, status=status.HTTP_200_OK)
    


class TaskStatusViewSet(viewsets.ModelViewSet):


    

    @csrf_exempt
    def get_task_status(self, request):
        try:
            user_id = request.GET.get('user_id')
            get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)

            task = TaskStatus.objects.filter(organization=get_org_id.organization_id).order_by('order')

            status_serializer = TaskStatusSerializer(task, many=True)
            print(status_serializer.data)

            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "User tasks status retrieved successfully.",
                "data": status_serializer.data
            }

            return JsonResponse(response)

        except EmployeePersonalDetails.DoesNotExist:
            response = {
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "EmployeePersonalDetails not found for the specified user.",
                "data": {}
            }
            return JsonResponse(response)

        except TaskStatus.DoesNotExist:
            response = {
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "TaskStatus not found for the specified organization.",
                "data": {}
            }
            return JsonResponse(response)

        except Exception as e:
            response = {
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"An error occurred: {str(e)}",
                "data": {}
            }
            return JsonResponse(response)
        

class TaskStatusNullDeleteViewSet(viewsets.ModelViewSet):


    

    @csrf_exempt
    def delete_null_status(self, request):
        user_id = request.GET.get('user_id')
        getTask = Tasks.objects.filter(status=None)
        # commented delete
        print(getTask)
        
        response = {
                "success": True,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
              
            }
        return JsonResponse(response)

    @csrf_exempt
    def add_personal_status(self, request):
        user_id = request.GET.get('user_id')
        users = User.objects.filter(user_role="Dev::Employee")
        
        try:
            for user in users:
                try:
                    
                    p_status = PersonalStatus.objects.get(user_id=user.id)
                    
                        
                except Exception as e:
                    
                    for status_data in [
                            {"status_name": "Pending", "fixed_state": "Pending", "color": "#fb9e00", "order": 1},
                            {"status_name": "InProgress", "fixed_state": "InProgress", "color": "#8585e0", "order": 2},
                            {"status_name": "Completed", "fixed_state": "Completed", "color": "#009ce0", "order": 3},
                            {"status_name": "Closed", "fixed_state": "Closed", "color": "#33cc33", "order": 4}
                        ]:
                            # PersonalStatus.objects.create(user_id=user, **status_data)
                            # commented 
                            pass
            return JsonResponse({
                "success": True,
             
            })
               
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to create status",
                "errors": str(e)
            })