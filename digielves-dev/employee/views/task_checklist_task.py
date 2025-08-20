from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from configuration.gzipCompression import compress
from digielves_setup.models import Board, SubTaskChild, SubTasks, EmployeePersonalDetails, Notification, TaskAction, TaskAttachments, TaskChecklist, TaskStatus, Tasks, User, notification_handler
from employee.seriallizers.attachment_seriallizers import AttachmentSerializer
from employee.seriallizers.board_seriallizer import UserSerializer
from employee.seriallizers.task_seriallizers import GetTask_subTaskSerializer, TaskChecklistSerializer, TaskChecklistTaskSerializer, UpdateTaskChecklistTaskSerializer
from employee.views.controllers.status_controllers import get_status_ids_from_assigned_side, get_status_ids_from_creater_side
from rest_framework import status
from rest_framework.decorators import api_view
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
class TasksinTaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskChecklistTaskSerializer


    @csrf_exempt
    def create_tasks_in_task(self,request):

        
        serializer = TaskChecklistTaskSerializer(data=request.data)

        try:
            if serializer.is_valid():
                
                task_checklist_task = serializer.save()
                
                assigned_users = task_checklist_task.Task.assign_to.all()
                # Set the assign_to field of the subtask to the assigned users
                task_checklist_task.assign_to.set(assigned_users)
                # Set system_assigned to True
                task_checklist_task.system_assigned = True
                task_checklist_task.save()




                try:
                    # Disconnect the post_save signal to prevent it from triggering during notifications creation
                    post_save.disconnect(notification_handler, sender=Notification)

                    notification = Notification.objects.create(
                        user_id=User.objects.get(id = request.data.get("user_id")),
                        where_to="customboard" if task_checklist_task.Task.checklist else "myboard",
                        notification_msg=f"You have been assigned a Sub Task: {task_checklist_task.task_topic}",
                        action_content_type=ContentType.objects.get_for_model(SubTasks),
                        action_id=task_checklist_task.id,
                        other_id=task_checklist_task.Task.checklist.board.id if task_checklist_task.Task.checklist else None,
                    )

                    # Set the notification_to field to the assigned users directly
                    notification.notification_to.set(assigned_users)

                    # Reconnect the post_save signal
                    post_save.connect(notification_handler, sender=Notification)
                    post_save.send(sender=Notification, instance=notification, created=True)

                except Exception as e:
                    print("-------------error")
                    print(e)
                    pass
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Task Checklist Task created successfully.",
                    "data": serializer.data
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create Task Checklist Task.",
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
    def get_task_in_tasks(self, request):
        try:
            user_id = request.GET.get('user_id')
            task_id = request.GET.get('task_id')

            if not task_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. check_id is missing."
                })

            subtasks = SubTasks.objects.filter(
                Q(assign_to=user_id) | Q(Task__created_by=user_id) | Q(created_by=user_id) | Q(Task__assign_to=user_id) 
                | Q(Q(subtaskchild__assign_to = user_id) & Q(subtaskchild__inTrash = False)) | Q(Task__checklist__board__assign_to=user_id),
                Task=task_id,
                inTrash=False
                
            ).order_by('created_at').distinct()     

            serializer = GetTask_subTaskSerializer(subtasks, many=True, context={'request': request})


            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Tasks in retrieved successfully.",
                "data": {
                    "subtasks": serializer.data
                }
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve Tasks.",
                "errors": str(e)
            })
            
    
    
    
    
    @csrf_exempt
    def get_unassigned_users_task_checklist_task(self, request):
        try:
            task_id = request.GET.get('task_id')
            user_id = request.GET.get('user_id')

            if not task_id or not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. Both task_id and user_id are required."
                })

            task = SubTasks.objects.filter(id=task_id).first()
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
            unassigned_users = User.objects.filter(employeepersonaldetails__organization_id=employee_details.organization_id,employeepersonaldetails__organization_location=employee_details.organization_location, verified=1,user_role="Dev::Employee",active=True).exclude(assign_to_task_checklist=task_id)

            
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
    def get_unassigned_users_task_checklist_task_customBoard(self, request):
        user_id = request.GET.get('user_id')
        board_id = request.GET.get('board_id')
        task_id = request.GET.get('task_id')

        try:
            board = Board.objects.get(id=board_id)

            assigned_users = board.assign_to.all()
            print(assigned_users)

            task = None
            if task_id:
                task = SubTasks.objects.get(id=task_id)

            unassigned_users = []
            for user in assigned_users:
                if task and task.assign_to.filter(id=user.id).exists():
                   
                    continue
                unassigned_users.append({
                    'user_id': user.id,
                    'email': user.email,
                    'firstname': user.firstname,
                    'lastname': user.lastname
                })

            response = {
                'success': True,
                'status': 200,
                'message': 'Users fetched successfully.',
                'data': unassigned_users
            }

            return compress(response)

        except Board.DoesNotExist:
            response = {
                'success': False,
                'status': 404,
                'message': 'Board not found.',
            }
            return JsonResponse(response)

        except Exception as e:
            response = {
                'success': False,
                'status': 500,
                'message': 'An error occurred while fetching users.',
                'error': str(e)
            }
            return JsonResponse(response)
    
    
    
    
    @csrf_exempt
    def UpdateChecklistTaskAssignTo(self, request):
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
                task = SubTasks.objects.get(id=task_id)
            except SubTasks.DoesNotExist:
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
            print(assign_users)
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
    
    
    @csrf_exempt
    def updateChecklistUserTasks(self, request):
        try:
            task_id = request.data.get('task_id')
            user_id = request.data.get('user_id')

            if not (task_id and user_id):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id and user_id are required."
                })

            task = SubTasks.objects.get(id=task_id)
            user_intance = User.objects.get(id=user_id)
            
            due_date = request.data.get('due_date')
            if due_date is not None:
                task.due_date = due_date
                
                TaskAction.objects.create(
                                    user_id=user_intance,
                                    task=task.Task,
                                    remark=f"Sub Task '{task.task_topic}' due date has been updated",
                                )
                
                
                try:    
                    post_save.disconnect(notification_handler, sender=Notification)
                    notification = Notification.objects.create(
                        user_id=user_intance,
                        where_to="customboard" if task.Task.checklist else "myboard",
                        notification_msg=f"Sub Task '{task.task_topic}' due date has been updated.",
                        action_content_type=ContentType.objects.get_for_model(Tasks),
                        action_id=task.Task.id,
                        other_id =task.Task.checklist.board.id if task.Task.checklist else None,
                        
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

                

            
            urgent_status = request.data.get('urgent_status')
            if urgent_status is not None:
                task.urgent_status = urgent_status
            
            desc = request.data.get('task_description')
            if desc is not None:
                task.task_description = desc
            
            topic = request.data.get('task_topic')
            if topic is not None:
                task.task_topic = topic
            
            Status = request.data.get('status')
        
            
            user_intance = User.objects.get(id=user_id)
            if Status is not None:
                fixed_state = {
                    # "Completed":"Completed",
                    "Closed": "Closed",
                    "Client Action Pending": "Client Action Pending",
                    "InReview" : "InReview"
                }
                fixed_states_to_include = fixed_state.values()
                get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)

                task_statuses = TaskStatus.objects.filter(fixed_state__in=fixed_states_to_include,organization=get_org_id.organization_id).order_by('order')

                fixed_state_ids = [Status.id for Status in task_statuses]
                got_task_statu = TaskStatus.objects.get(id=Status)
            
                if got_task_statu.id in fixed_state_ids:
                    
                    checklist_task_check = SubTasks.objects.filter(Q(~Q(created_by=user_id)) & Q(assign_to=user_id), id=task.id).distinct().first()
                   
                    checklist_task_check_oob = SubTasks.objects.filter(Q(~Q(created_by=user_id)) & Q(~Q(assign_to=user_id)), id=task.id).distinct().first() # oob - Out of box 
                    
                    task_owner = SubTasks.objects.filter(Task__created_by=user_id, id=task.id).distinct().first()
                    if task_owner:
                        pass
                    elif checklist_task_check:
                        return JsonResponse({
                            "success": True,
                            "status": 124,
                            "message": "Permission denied: Unable to change the task status to Done."
                        })
                    elif checklist_task_check_oob:
                        return JsonResponse({
                            "success": True,
                            "status": 124,
                            "message": "Permission denied: Unable to change status."
                        })
                    else:
                        pass
                else:
                    
                    before_task_updated_status = task.status
                    opened_status_ids = get_status_ids_from_assigned_side(user_id)
                    int_status = int(Status)
                    if before_task_updated_status.id in opened_status_ids and int_status not in opened_status_ids:
                        closed_status_ids = get_status_ids_from_creater_side(user_id, True)
                        to_close_task_subtask_child = SubTaskChild.objects.filter(subtasks=task, inTrash= False).distinct().count()
                

                        to_close_task_subtask_child_with_status = len(SubTaskChild.objects.filter(subtasks=task,status__in=closed_status_ids, inTrash= False).distinct())
                        
                        if to_close_task_subtask_child != to_close_task_subtask_child_with_status:
                            
                        
                            response = {
                                "success": True,
                                "status": 124,
                                "message": "Unable to update sub task status: The status of one or more sub-tasks child differs from the main sub task."
                            }


                            return JsonResponse(response)
                        
                
                TaskAction.objects.create(
                                    user_id=user_intance,
                                    task=task.Task,
                                    remark=f"Sub Task '{task.task_topic}' status has been updated {task.status.status_name} to {got_task_statu.status_name}",
                                )
                
                
                
                try:    
                    post_save.disconnect(notification_handler, sender=Notification)
                    notification = Notification.objects.create(
                        user_id=user_intance,
                        where_to="customboard" if task.Task.checklist else "myboard",
                        notification_msg=f"Sub Task '{task.task_topic}' Status has been updated {task.status.status_name} to {got_task_statu.status_name}",
                        action_content_type=ContentType.objects.get_for_model(Tasks),
                        action_id=task.Task.id,
                        other_id =task.Task.checklist.board.id if task.Task.checklist else None,
                        
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
                
                


                
                
                task.status = got_task_statu

            
            assign_to = request.data.get('assign_to')
            if assign_to is not None:
                try:
                    assign_user_ids = [int(user_id) for user_id in assign_to.split(',') if user_id.strip()]
                except ValueError:
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid user IDs format",
                    })

                assign_users = User.objects.filter(id__in=assign_user_ids)
                

            
                try:    
                    post_save.disconnect(notification_handler, sender=Notification)
                    
                    # Get currently assigned users
                    current_assigned_users = set(task.assign_to.all())

                    # Determine new users to notify
                    new_users_to_notify = [user for user in assign_users if user not in current_assigned_users]

                    notification = Notification.objects.create(
                        user_id=user_intance,
                        where_to="customboard" if task.Task.checklist else "myboard",
                        notification_msg=f"You have been assigned a Sub Task: {task.task_topic}",
                        action_content_type=ContentType.objects.get_for_model(Tasks),
                        action_id=task.Task.id,
                        other_id =task.Task.checklist.board.id if task.Task.checklist else None,
                        
                    )
                    

                    notification.notification_to.set(new_users_to_notify)
                        
                        
                    post_save.connect(notification_handler, sender=Notification)
                    post_save.send(sender=Notification, instance=notification, created=True)
                    task.assign_to.set(assign_users)
                except Exception as e:
                    print("-------------error")
                    print(e)
                    pass
                
            task.save()

            # serializer = UpdateTaskChecklistTaskSerializer(task)

            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task updated successfully.",
                # "data": serializer.data
            }

            return compress(response)

        except SubTasks.DoesNotExist:
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

    @csrf_exempt
    def delete_checklistTaskData(self, request):
        task_id = request.GET.get('task_id')
        user_id = request.GET.get('user_id')
        print(task_id)
        try:
            task = SubTasks.objects.get(id=task_id,created_by=user_id)
        except SubTasks.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Tasks not found",
            })
        print(task)
        task.inTrash = True
        task.trashed_with="Manually"
        task.save()
        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "Tasks Moved successfully",
        })  