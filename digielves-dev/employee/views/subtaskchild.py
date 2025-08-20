from digielves_setup.models import Board, Notification, SubTaskChild, SubTasks, TaskAction, TaskStatus, Tasks, User, notification_handler
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
class SubTaskChildViewSet(viewsets.ModelViewSet):
    
    
    @csrf_exempt
    def create_subtask_child(self, request):
        data = request.data.copy()
        
        # Replace user_id with created_by
        if 'user_id' in data:
            user_ids = data.pop('user_id')
            
            data['created_by'] = user_ids[0]

        serializer = CreateSubTaskChildSerializer(data=data)
        if serializer.is_valid():
            subtask_child = serializer.save()
            assigned_users = subtask_child.subtasks.assign_to.all()
            # Set the assign_to field of the subtask to the assigned users
            if assigned_users:
                subtask_child.assign_to.set(assigned_users)
            else:
                assigned_users = subtask_child.subtasks.Task.assign_to.all()
                subtask_child.assign_to.set(assigned_users)
            # Set system_assigned to True
            subtask_child.system_assigned = True
            subtask_child.save()
            
            
            try:
                # Disconnect the post_save signal to prevent it from triggering during notifications creation
                post_save.disconnect(notification_handler, sender=Notification)

                notification = Notification.objects.create(
                    user_id=User.objects.get(id = request.data.get("user_id")),
                    where_to="customboard" if subtask_child.subtasks.Task.checklist else "myboard",
                    notification_msg=f"You have been assigned a Sub Task Child: {subtask_child.task_topic}",
                    action_content_type=ContentType.objects.get_for_model(SubTasks),
                    action_id=subtask_child.id,
                    other_id=subtask_child.subtasks.Task.checklist.board.id if subtask_child.subtasks.Task.checklist else None,
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
                    "status": status.HTTP_201_CREATED
                })
        else:
            
            return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "errors": serializer.errors
                })
        
     
            
    
    @csrf_exempt
    def get_subtask_child(self, request):
        subtask_id = request.GET.get('subtask_id')
        user_id = request.GET.get('user_id')

        try:
            user_instance = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found",
            })

        try:
            sub_task = SubTasks.objects.get(id=subtask_id)
        except SubTasks.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Subtask not found",
            })

        data = SubTaskChild.objects.filter(subtasks=sub_task, inTrash= False)
        serializer = GetSubTaskChildSerializer(data, many=True)

        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,
            "data": serializer.data
        })
    
    @csrf_exempt
    def UpdateSubTaskChild(self, request):
        try:
            subtaskchild = request.data.get('child_task_id')
            user_id = request.data.get('user_id')
            user_intance = User.objects.get(id=user_id)
            if not subtaskchild:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. subtask_id is missing.",
                })

            try:
                task = SubTaskChild.objects.get(id=subtaskchild)
            except SubTaskChild.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task not found",
                })

            assign_user_ids_str = request.data.get('assign_to', '')
            if assign_user_ids_str:            

                try:
                    assign_user_ids = [int(user_id) for user_id in assign_user_ids_str.split(',') if user_id.strip()]
                except ValueError:
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid user IDs format",
                    })

                
                try:    
                    post_save.disconnect(notification_handler, sender=Notification)
                    
                    # Get currently assigned users
                    current_assigned_users = set(task.assign_to.all())
                    assign_users = User.objects.filter(id__in=assign_user_ids)
                    # Determine new users to notify
                    new_users_to_notify = [user for user in assign_users if user not in current_assigned_users]

                    notification = Notification.objects.create(
                        user_id=user_intance,
                        where_to="customboard" if task.subtasks.Task.checklist else "myboard",
                        notification_msg=f"You have been assigned a Sub Task Child: {task.task_topic}",
                        action_content_type=ContentType.objects.get_for_model(Tasks),
                        action_id=task.subtasks.Task.id,
                        other_id =task.subtasks.Task.checklist.board.id if task.subtasks.Task.checklist else None,
                        
                    )
                    

                    notification.notification_to.set(new_users_to_notify)
                        
                        
                    post_save.connect(notification_handler, sender=Notification)
                    post_save.send(sender=Notification, instance=notification, created=True)
                    
                    task.assign_to.set(assign_users)
                except Exception as e:
                    print("-------------error")
                    print(e)
                    pass
                
                
                
                                
            due_date = request.data.get('due_date')
            if due_date is not None:
                task.due_date = due_date
                TaskAction.objects.create(
                                    user_id=user_intance,
                                    task=task.subtasks.Task,
                                    remark=f"Sub Task child '{task.task_topic}' due date has been updated",
                                )
                
                try:    
                    post_save.disconnect(notification_handler, sender=Notification)
                    notification = Notification.objects.create(
                        user_id=user_intance,
                        where_to="customboard" if task.subtasks.Task.checklist else "myboard",
                        notification_msg=f"Sub Task child '{task.task_topic}' due date has been updated.",
                        action_content_type=ContentType.objects.get_for_model(Tasks),
                        action_id=task.subtasks.Task.id,
                        other_id =task.subtasks.Task.checklist.board.id if task.subtasks.Task.checklist else None,
                        
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
            if Status is not None:
                closed_status_ids = get_status_ids_from_creater_side(user_id)
                got_task_status = TaskStatus.objects.get(id=Status)

                
                if got_task_status.id in closed_status_ids:

                    #  conditions
                    combined_condition = (
                        ~Q(assign_to=user_id) & (
                            Q(created_by=user_id) |
                            Q(subtasks__created_by=user_id) |
                            Q(subtasks__Task__created_by=user_id)|
                            Q(subtasks__Task__checklist__board__assign_to=user_id)|
                            Q(subtasks__Task__checklist__board__created_by=user_id)
                        )
                    )
                    # Filter the SubTaskChild objects using the condition
                    subtask_child = SubTaskChild.objects.filter(combined_condition, id=task.id).distinct().first()

                    if subtask_child:
                        if str(task.status.status_name) != str(got_task_status.status_name):
                            TaskAction.objects.create(
                                        user_id=user_intance,
                                        task=task.subtasks.Task,
                                        remark=f"Sub Task child'{task.task_topic}' status has been updated {task.status.status_name} to {got_task_status.status_name}",
                                    )
                            
                            try:    
                                post_save.disconnect(notification_handler, sender=Notification)
                                notification = Notification.objects.create(
                                    user_id=user_intance,
                                    where_to="customboard" if task.subtasks.Task.checklist else "myboard",
                                    notification_msg=f"Sub Task child '{task.task_topic}' Status has been updated {task.status.status_name} to {got_task_status.status_name}",
                                    action_content_type=ContentType.objects.get_for_model(Tasks),
                                    action_id=task.subtasks.Task.id,
                                    other_id =task.subtasks.Task.checklist.board.id if task.subtasks.Task.checklist else None,
                                    
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
                        task.status = got_task_status
                            
                    else:
                        return JsonResponse({
                            "success": False,
                            "status": 124,
                            "message": f"Permission denied: Unable to change status to {got_task_status.status_name}."
                        })
                else:

                    if str(task.status.status_name) != str(got_task_status.status_name):
                        TaskAction.objects.create(
                                        user_id=user_intance,
                                        task=task.subtasks.Task,
                                        remark=f"Sub Task child'{task.task_topic}' status has been updated {task.status.status_name} to {got_task_status.status_name}",
                                    )
                    
                    
    
                
                        try:    
                            post_save.disconnect(notification_handler, sender=Notification)
                            notification = Notification.objects.create(
                                user_id=user_intance,
                                where_to="customboard" if task.subtasks.Task.checklist else "myboard",
                                notification_msg=f"Sub Task child '{task.task_topic}' Status has been updated {task.status.status_name} to {got_task_status.status_name}",
                                action_content_type=ContentType.objects.get_for_model(Tasks),
                                action_id=task.subtasks.Task.id,
                                other_id =task.subtasks.Task.checklist.board.id if task.subtasks.Task.checklist else None,
                                
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
                    
                    task.status = got_task_status
                          
            task.save()

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "errors": str(e),
            })
    
    
    @csrf_exempt
    def delete_subTask_child(self, request):
        task_id = request.GET.get('task_child_id')
        user_id = request.GET.get('user_id')
        try:
            combined_condition = (
                        ~Q(assign_to=user_id) & (
                            Q(created_by=user_id) |
                            Q(subtasks__created_by=user_id) |
                            Q(subtasks__Task__created_by=user_id)|
                            Q(subtasks__Task__checklist__board__created_by=user_id)
                        )
                    )
            task = SubTaskChild.objects.get(
                combined_condition,
                id=task_id)
        except SubTaskChild.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Tasks not found",
            })
        task.inTrash = True
        task.trashed_with="Manually"
        task.save()
        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "Tasks Moved successfully",
        })  