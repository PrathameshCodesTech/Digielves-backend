
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from digielves_setup.helpers.error_trace import create_error_response
from digielves_setup.models import Board, Category, Checklist, EmployeePersonalDetails, FevBoard, Meettings, Notification, SavedCategory, SavedTemplateChecklist, SavedTemplateTaskList, SavedTemplates,TestSavedTemplate, PersonalStatus, PersonalTask, TaskChecklist, TaskHierarchy, TaskHierarchyAttachments, TaskHierarchyAction, TaskHierarchyChatting, TaskHierarchyChecklist, TaskHierarchyComments, TaskHierarchyDueRequest, TaskSpecialAccess, TaskStatus, Template, TemplateChecklist, TemplateTaskList, User, UserFilters, notification_handler, UserCreation, ReportingRelationship
from employee.seriallizers.personal_board.personal_board_seriallizers import GetPersonalTaskOnMyDaySerializer
from employee.seriallizers.task_hierarchy.task_hierarchy_seriallizers import CombinedTaskHierarchySerializer, CombinedTaskMeetingSerializer, CreateTaskHierarchySerializer, CustomBoardTaskHierarchyGetSerializer, GetBoardsInHierarchySerializer, GetDueDateRequestSerializer, GetTaskHierarchySerializer, InTaskHierarchyBoardSerializers, MeettingsCustomSerializer, MyDayTaskHierarchyGetSerializer, TaskHierarchyChildrenSerializer, TaskHierarchyCustomSerializer, mydayUserSerializers
from employee.views.controllers.status_controllers import get_status_ids_from_assigned_side, get_status_ids_from_creater_side
from rest_framework import status
from rest_framework import viewsets



from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.db import transaction

import threading

from django.core.serializers import serialize
from django.db.models import Q
import pytz
from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from datetime import datetime, timedelta
from configuration.gzipCompression import compress


from django.db.models import Case, When, Value, CharField, IntegerField,FloatField, F
from django.db.models.functions import Cast
from django.db.models.functions import Concat
from configuration import settings
import os
import threading
from itertools import chain
from django.shortcuts import get_object_or_404
class TaskHierarchyViewSet(viewsets.ModelViewSet):
    
    @csrf_exempt
    def create_task(self, request):
        serializer = CreateTaskHierarchySerializer(data=request.data)

        if not serializer.is_valid():
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to create Task.",
                "errors": serializer.errors
            })

        try:
            with transaction.atomic():
                repeat_task = request.data.get('repeat_task', 'false').lower() == 'true' or request.data.get('repeat_task', 'false').lower() == True
                if not repeat_task:
                    task = serializer.save()
                    checklist_id = request.data.get('checklist')
                    if checklist_id:
                        checklist = Checklist.objects.get(id=checklist_id)
                        task.checklist = checklist

                    due_date_date = request.data.get('due_date')
                    if due_date_date:
                        task.due_date = due_date_date

                    assigned_users = request.data.get('assign_to', '')
                    if assigned_users:
                        assign_user_ids = list(map(int, assigned_users.split(',')))
                        assign_users = User.objects.filter(id__in=assign_user_ids)
                        task.assign_to.set(assign_users)

                    depend_on_str = request.data.get('depend_on', '')
                    if depend_on_str:
                        depends_on_ids = list(map(int, depend_on_str.split(',')))
                        depends_on_tasks = TaskHierarchy.objects.filter(id__in=depends_on_ids)
                        task.depend_on.set(depends_on_tasks)

                    parent_task_id = request.data.get('parent_task_id')
                    if parent_task_id:
                        parent_task = TaskHierarchy.objects.filter(id=parent_task_id).first()
                        if parent_task:
                            task.parent = parent_task
                            task.task_level = parent_task.task_level + 1
                            task.save()

                    if not parent_task_id:
                        self.handle_attachments(request, task)

                    if assigned_users:
                        t = threading.Thread(target=self.handle_non_dependent, args=(request, task, assign_user_ids, checklist_id))
                        t.setDaemon(True)
                        t.start()

                    task.save()

                    return JsonResponse({
                        "success": True,
                        "status": status.HTTP_201_CREATED,
                        "message": "Task created successfully.",
                        "data": {
                            "task_id": task.id,
                            "board_id": task.checklist.board.id if task.checklist else None
                        }
                    })
                
                else:
                    
                    from_due_date_str = request.data.get('from_due_date')
                    to_due_date_str = request.data.get('to_due_date')
                    to_due_time_str = request.data.get('to_due_time')
                    included_weekdays_str = request.data.get('included_weekdays', '')
                    from_due_date = datetime.strptime(from_due_date_str, '%Y-%m-%d').date()
                    to_due_date = datetime.strptime(to_due_date_str, '%Y-%m-%d').date()
                    included_weekdays = [int(day) for day in included_weekdays_str.split(',') if day]

                    remaining_dates = self.calculate_remaining_weekdays(from_due_date, to_due_date, included_weekdays)
                    assigned_users = request.data.get('assign_to', '')
                    if assigned_users:
                        assign_user_ids = list(map(int, assigned_users.split(',')))
                        assign_users = User.objects.filter(id__in=assign_user_ids)

                    depend_on_str = request.data.get('depend_on', '')
                    if depend_on_str:
                        depends_on_ids = list(map(int, depend_on_str.split(',')))
                        depends_on_tasks = TaskHierarchy.objects.filter(id__in=depends_on_ids)

                    checklist_id = request.data.get('checklist')
                    checklist = Checklist.objects.get(id=checklist_id) if checklist_id else None
                    first_task_id = None
                    
                    for remaining_date_str in remaining_dates:
                        remaining_date = datetime.strptime(remaining_date_str, '%Y-%m-%d').date()
                        due_datetime_str = f"{remaining_date}T{to_due_time_str}"
                        creater = User.objects.get(id =request.data.get('created_by'))
                        new_task = TaskHierarchy(
                            checklist=checklist,
                            due_date=due_datetime_str,
                            task_topic=request.data.get('task_topic'),
                            created_by=creater,
                            task_description=request.data.get('task_description'),
                            urgent_status= True if request.data.get('urgent_status') == "true" or request.data.get('urgent_status') == True else False,
                        )
                        new_task.save()

                        if assigned_users:
                            new_task.assign_to.set(assign_users)
                        if depend_on_str:
                            new_task.depend_on.set(depends_on_tasks)

                        self.handle_attachments(request, new_task)
                        if first_task_id is None:
                            first_task_id = new_task.id
                    
                    
                    first_task = TaskHierarchy.objects.get(id=first_task_id)
                    
                    if assigned_users:
                        t = threading.Thread(target=self.handle_notifications_for_repeat_task, args=(request,first_task,assign_user_ids, checklist_id))
                        t.setDaemon(True)
                        t.start()
                    
                    
                    
                    return JsonResponse({
                        "success": True,
                        "status": status.HTTP_201_CREATED,
                        "message": "Repeating tasks created successfully.",
                        "data": {
                        "task_id": first_task_id,
                        "board_id": first_task.checklist.board.id if first_task.checklist else None
                    }
                    })

                    
                
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)


    def handle_non_dependent(self, request, task,assign_user_ids ,checklist_id):
        
        self.handle_notifications(request, task, assign_user_ids, checklist_id)
        
        
    def handle_attachments(self, request, task):
        attachments = request.FILES.getlist('attachments')
        for attachment in attachments:
            try:
                TaskHierarchyAttachments.objects.create(task=task, task_attachment=attachment)
            except Exception as e:
                print("🐍 File: task_hierarchy/task.py | Line: 90 | handle_attachments ~ e",e)
               


    def handle_notifications(self, request, task, assign_user_ids, checklist_id):
        try:
            assign_users = User.objects.filter(id__in=assign_user_ids)
            if request.data.get("created_by") not in assign_users:
                post_save.disconnect(notification_handler, sender=Notification)
                notification = Notification.objects.create(
                    user_id=request.user,
                    where_to="customboard" if checklist_id else "myboard",
                    notification_msg=f"A new task has been assigned to you: {task.task_topic}",
                    action_content_type=ContentType.objects.get_for_model(TaskHierarchy),
                    action_id=task.id,
                    other_id=checklist_id if checklist_id else None
                )
                notification.notification_to.set(assign_users)
                post_save.connect(notification_handler, sender=Notification)
                post_save.send(sender=Notification, instance=notification, created=True)
        except Exception as e:
            print(f"Exception in handle_notifications: {e}")
            
    def handle_notifications_for_repeat_task(self, request, task, assign_user_ids, checklist_id):
        try:
            assign_users = User.objects.filter(id__in=assign_user_ids)
            if request.data.get("created_by") not in assign_users:
                post_save.disconnect(notification_handler, sender=Notification)
                notification = Notification.objects.create(
                    user_id=request.user,
                    where_to="customboard" if checklist_id else "myboard",
                    notification_msg=f"A new repeat task has been assigned to you: {task.task_topic}",
                    action_content_type=ContentType.objects.get_for_model(TaskHierarchy),
                    action_id=task.id,
                    other_id=checklist_id if checklist_id else None
                )
                notification.notification_to.set(assign_users)
                post_save.connect(notification_handler, sender=Notification)
                post_save.send(sender=Notification, instance=notification, created=True)
        except Exception as e:
            print(f"Exception in handle_notifications: {e}")
    
    def calculate_remaining_weekdays(self, from_date, to_date, included_weekdays):
        current_date = from_date
        remaining_weekdays = []

        while current_date <= to_date:
            if current_date.weekday() in included_weekdays:
                remaining_weekdays.append(str(current_date))
            current_date += timedelta(days=1)

        return remaining_weekdays
    
    @csrf_exempt
    def get_task_assigned_users(self,request):
        try:
            
            task_id = request.GET.get('task_id')
            user_id = request.GET.get('user_id')
            task = get_object_or_404(TaskHierarchy, id=task_id)


            assigned_users = task.assign_to.all()

            serializer = mydayUserSerializers(assigned_users, many=True)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Tasks in retrieved successfully.",
                "data": serializer.data
            })

        except TaskHierarchy.DoesNotExist:
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
    def update_task_to_other_checklist(self, request):
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

            task = TaskHierarchy.objects.get(id=task_id)

        

            checklist = Checklist.objects.get(id=checklist_id)
            
            if sequence is not None:
                try:
                    sequence = float(sequence)
                except ValueError:
                    sequence = None

                if sequence is not None and sequence <= 0.000005:
                    # Update the sequences of tasks in the checklist with consecutive values starting from 5
                    checklist_tasks = TaskHierarchy.objects.filter(checklist=checklist).order_by('sequence')
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
                
            }

            return JsonResponse(response)

        except TaskHierarchy.DoesNotExist:
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
            


        
    @csrf_exempt
    def get_myboard_task(self, request):

      
        user_id = request.GET.get('user_id')

        if not user_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. user_id is missing."
            })
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found."
            })

        #  Step 1: Fetch Reporting User IDs (Safe Fallback)
        try:
            reporting_user_ids = list(
                ReportingRelationship.objects.filter(
                    reporting_to_user__employee_user_id=user_id
                ).values_list('reporting_user__employee_user_id', flat=True)
            )
        except Exception as e:
          reporting_user_ids = []
        
        print("?? File: task_hierarchy/task.py | Line: 382 | get_myboard_task ~ reporting_user_ids",reporting_user_ids)

        # Step 2: Modify Task Query (Safely Include Reporting IDs)
        tasks = TaskHierarchy.objects.filter(
            (
        Q(created_by=user_id) |
        Q(assign_to=user_id) |
        Q(created_by__in=reporting_user_ids) |
        Q(assign_to__id__in=reporting_user_ids)
    ),
            
            checklist__isnull=True, is_personal=False, inTrash=False, status__isnull=False
        ).distinct().order_by('due_date')
        
        
        
        main_tasks = set()

        for task in tasks:
            main_task = task
            while main_task.parent is not None:
                main_task = main_task.parent
            
            if main_task.checklist is None: 
                main_tasks.add(main_task)
        all_tasks = {f"t_{task.id}" for task in main_tasks}
        

        
        try:
            org_details = EmployeePersonalDetails.objects.get(user_id=user_id)
            task_statuses = TaskStatus.objects.filter(
                organization=org_details.organization_id
            ).order_by('order', 'created_at')
        except EmployeePersonalDetails.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Organization details not found."
            })

        fixed_state_titles_and_ids = [(Status.status_name,Status.fixed_state,Status.order ,Status.id) for Status in task_statuses]

        data = [
            {"id": f"s_{status_id}", "title": title,"fixed_state":fix_state,"order": order, "status_id": status_id, "tasks": []}
            for  idx, (title,fix_state, order ,status_id) in enumerate(fixed_state_titles_and_ids)
        ]

        # closed_status_ids = get_status_ids_from_creater_side(user_id, True)
        
        IST = pytz.timezone('Asia/Kolkata')

        for task_id in all_tasks:
            task_num = int(task_id.split("_")[1])
            task = TaskHierarchy.objects.get(id=task_num)
            
            

            
            created_by_data = {
                "id": task.created_by.id,
                "email": task.created_by.email,
                "firstname": task.created_by.firstname,
                "lastname": task.created_by.lastname,
            }

            due_date_ist = task.due_date.astimezone(IST) if task.due_date else None
            assign_to_data = [{
                    "id": user.id,
                    "email": user.email,
                    "firstname": user.firstname,
                    "lastname": user.lastname
                } for user in task.assign_to.all()]
            
           
            depend_on = [task.id for task in task.depend_on.all()]
            
            progress_percentage, division = self.calculate_progress_and_division(task)
            
            # Step 3: Add is_reporting Flag in Task Loop (No Crash Guarantee)
            try:
                is_reporting = (
                    task.created_by.id in reporting_user_ids or
                    any(assignee.id in reporting_user_ids for assignee in task.assign_to.all())
                )
            except Exception:   
                is_reporting = False
            task_data = {
                "id": task_id,
                "title": task.task_topic,
                "checklist": task.checklist.id if task.checklist else None,
                "description": task.task_description,
                "due_date": due_date_ist.strftime('%Y-%m-%d %H:%M:%S%z') if due_date_ist else None,
                "urgent_status": task.urgent_status,
                "status": task.status,
                "start_date": task.start_date,
                "end_date": task.end_date,
                "reopened_count": task.reopened_count,
                "created_at": task.created_at.isoformat(),
                "created_by": created_by_data,
                "depend_on": depend_on,
                "assign_to": assign_to_data,
                "progress_percentage": progress_percentage,
                "division": division,
                "is_reporting": is_reporting,
            }
            
            for idx, (title, fix_state, order, status_id) in enumerate(fixed_state_titles_and_ids):
                if task.status and task.status.id == status_id:
                    task_data["status"] = {
                        "id": task.status.id,
                        "status_name": task.status.status_name,
                        "fixed_state": task.status.fixed_state,
                        "color": task.status.color,
                    }
                    data[idx]["tasks"].append(task_data)
                    break

        for section in data:
            section["tasks"] = [task for task in section["tasks"] if task.get("due_date")]
            section["tasks"].sort(key=lambda task: task["due_date"])

                
            # section["tasks"] = sorted(section["tasks"], key=lambda task: task.get("due_date").isoformat() if task.get("due_date") else "")

        
        try:
            board_view = UserFilters.objects.get(user=user_id).myboard_view
        except Exception as e:
            board_view = None
        
        users_with_access_gave = TaskSpecialAccess.objects.filter(user=user).select_related('access_to')
        
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

        return JsonResponse(response, encoder=self.DateTimeEncoder)
    
    
    
    def serialize_status_info(self, status_info):
        return {
            "id": status_info["id"],
            "status_name": status_info["status_name"],
            "color": status_info["color"],
        }
        
    class DateTimeEncoder(DjangoJSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)
    
    
        
    def calculate_progress_and_division(self, task):
        SubTask = TaskHierarchy.objects.filter(parent=task, inTrash=False)
        total_duration_to_due_date = timedelta()
        for subtask_task in SubTask:
            due_date = subtask_task.due_date
            if due_date:
                now = timezone.localtime(timezone.now())
                duration_to_due_date = due_date - now
                total_duration_to_due_date += duration_to_due_date


        total_subtask_task = SubTask.count()
        closed_status_ids = get_status_ids_from_creater_side(task.created_by.id, True)
        completed_subtask_task = SubTask.filter(status__id__in=closed_status_ids)
        total_duration_completed = timedelta()

        for subtask_task in completed_subtask_task:
            due_date = subtask_task.due_date
            if due_date:
                now = timezone.localtime(timezone.now())
                duration_to_due_date = due_date - now
                total_duration_completed += duration_to_due_date

        progress_percentage = 100
        if total_duration_to_due_date.total_seconds() > 0:
            if task.status and task.status.id in closed_status_ids:
                pass
            else:
                progress_percentage = round((total_duration_completed.total_seconds() / total_duration_to_due_date.total_seconds()) * 100, 2)
        elif task.status and task.status.id in closed_status_ids:
            progress_percentage = 100
        else:
            progress_percentage = 0

        division = f"{completed_subtask_task.count()}/{total_subtask_task}"
        return max(progress_percentage, 0), division
    
    
    
    
    
    @csrf_exempt
    def change_task_status(self, request):
        try:
            task_id = request.data.get('task_id')
            status_id = request.data.get('status')
            user_id = request.data.get('user_id')

            if not task_id or not status_id or not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id, status, or user_id is missing."
                })

           

            try:
                new_status = TaskStatus.objects.get(id=status_id)
            except TaskStatus.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Status not found."
                })
                
            closed_status_ids = get_status_ids_from_creater_side(user_id)

            with transaction.atomic():
                try:
                    task = TaskHierarchy.objects.select_for_update().get(id=task_id)

                    if new_status.id in closed_status_ids:
                        tasks = TaskHierarchy.objects.filter(
                            Q(~Q(created_by=user_id) & Q(assign_to=user_id)),
                            id=task_id
                        ).distinct().first()

                        if tasks:
                            return JsonResponse({
                                "success": True,
                                "status": 124,
                                "message": f"Permission denied: Unable to change the task status to {new_status.status_name}."
                            })

                        tasks_oob = TaskHierarchy.objects.filter(
                            Q(~Q(created_by=user_id) & Q(~Q(assign_to=user_id))),
                            id=task_id
                        ).distinct().first()

                        if tasks_oob:  # out of box
                            return JsonResponse({
                                "success": True,
                                "status": 124,
                                "message": "Permission denied."
                            })

                    user= User.objects.get(id = user_id)
                    if not (task.created_by == user or task.assign_to.filter(id=user_id).exists()):
                        
                        
                        return JsonResponse({
                            "success": False,
                            "status": 403,
                            "message": "You don't have permission to update this task.",
                        })

                    current_status_id = task.status.id if task.status else None
                    
                    closed_status_ids_with_complete = get_status_ids_from_creater_side(user_id, True)
                    assigned_side_ids = get_status_ids_from_assigned_side(user_id)

                    
                    if int(status_id) in closed_status_ids_with_complete:
                        if not task.status_changed_to_complete:
                            task.status_changed_to_complete=True
                            task.end_date = timezone.now()
                        
                    # Check if dependent tasks are complete
 
                    if int(status_id) in closed_status_ids_with_complete:
                        
                        if not self.dependent_tasks_complete(task, closed_status_ids_with_complete):
                        
                            return JsonResponse({
                                "success": True,
                                "status": 123,
                                "message": "Unable to update task status: One or more dependent tasks are incomplete."
                            })
                        
                    
                    
                    
                    if current_status_id in assigned_side_ids and int(status_id) not in assigned_side_ids:
                        if self.task_checklist_incomplete(task):
                            return JsonResponse({
                                "success": True,
                                "status": 123,
                                "message": "Unable to update task status: checklist is incomplete."
                            })

                        # check_in_assignee_side = get_status_ids_from_assigned_side(user_id, True)
                        if self.task_subtasks_incomplete(task, closed_status_ids_with_complete):
                            return JsonResponse({
                                "success": True,
                                "status": 123,
                                "message": "Unable to update task status: The status of one or more sub-tasks differs from the main task."
                            })
                    
                    should_skip_notification = self.handle_task_status_update(task, new_status, user, current_status_id, closed_status_ids_with_complete, request)
                    task.status = new_status
                    task.save()
                    if current_status_id != new_status.id and not should_skip_notification:
                        t = threading.Thread(target=self.create_task_status_notification, args=(request, task, new_status))
                        t.setDaemon(True) 
                        t.start()

                    response = {
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "message": "Task status updated successfully.",
                    }

                    return JsonResponse(response)

                except TaskHierarchy.DoesNotExist:
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": "Task not found.",
                    })

        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    def task_checklist_incomplete(self, task):
        total_checklist = TaskHierarchyChecklist.objects.filter(Task=task, inTrash=False).count()
        completed_checklist = TaskHierarchyChecklist.objects.filter(Task=task, completed=True, inTrash=False).count()
        return total_checklist != completed_checklist
    
    
    def handle_task_status_update(self, task, new_status, user, current_status_id, closed_status_ids, request):
        if current_status_id in closed_status_ids and new_status.id not in closed_status_ids:
            task.reopened_count += 1
            task.status_changed_to_complete=False
            task.end_date = None
            TaskHierarchyAction.objects.create(
                user_id=user,
                task=task,
                remark=f"Task has been reopened from {task.status.status_name} to {new_status.status_name}",
            )
            t = threading.Thread(target=self.reopened_status_notification, args=(request, task, new_status))
            t.setDaemon(True) 
            t.start()
            return True
        elif current_status_id != new_status.id:
            TaskHierarchyAction.objects.create(
                user_id=user,
                task=task,
                remark=f"Task status has been updated from {task.status.status_name} to {new_status.status_name}",
            )
            return False
        return False
    def task_subtasks_incomplete(self, task, complete_status_ids):
        total_subtasks = TaskHierarchy.objects.filter(parent=task, inTrash=False).count()
        completed_subtasks = TaskHierarchy.objects.filter(parent=task, status__in=complete_status_ids, inTrash=False).count()
        return total_subtasks != completed_subtasks

    def dependent_tasks_complete(self, task, complete_status_ids):
        dependent_tasks = task.depend_on.filter(inTrash=False)
        for dep_task in dependent_tasks:
            if dep_task.status.id not in complete_status_ids:
                return False
        return True
    
    
    def create_task_status_notification(self, request, task, new_status):
        try:
            post_save.disconnect(notification_handler, sender=Notification)
            notification = Notification.objects.create(
                user_id=request.user,
                where_to="customboard" if task.checklist else "myboard",
                notification_msg=f"Task '{task.task_topic}' Status has been updated to {new_status.status_name}",
                action_content_type=ContentType.objects.get_for_model(TaskHierarchy),
                action_id=task.id
            )

            if str(request.data.get('user_id')) == str(task.created_by.id):
                notification.notification_to.set(task.assign_to.all())
            else:
                notification.notification_to.add(task.created_by)
                assigned_users = task.assign_to.exclude(id=request.data.get('user_id')).all()
                notification.notification_to.add(*assigned_users)

            post_save.connect(notification_handler, sender=Notification)
            post_save.send(sender=Notification, instance=notification, created=True)
        except Exception as e:
            pass
    
    def reopened_status_notification(self, request, task, new_status):
        try:
            post_save.disconnect(notification_handler, sender=Notification)
            notification = Notification.objects.create(
                user_id=request.user,
                where_to="customboard" if task.checklist else "myboard",
                notification_msg=f"Task '{task.task_topic}' has been reopened from {task.status.status_name} to {new_status.status_name}",
                action_content_type=ContentType.objects.get_for_model(TaskHierarchy),
                action_id=task.id
            )

            if str(request.data.get('user_id')) == str(task.created_by.id):
                notification.notification_to.set(task.assign_to.all())
            else:
                notification.notification_to.add(task.created_by)
                assigned_users = task.assign_to.exclude(id=request.data.get('user_id')).all()
                notification.notification_to.add(*assigned_users)

            post_save.connect(notification_handler, sender=Notification)
            post_save.send(sender=Notification, instance=notification, created=True)
        except Exception as e:
            pass
    
    
    
    @csrf_exempt
    def update_user_tasks(self, request):
        try:
            task_id = request.data.get('task_id')
            user_id = request.data.get('user_id')

            if not task_id or not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id and user_id are required."
                })

            try:
                task = TaskHierarchy.objects.get(id=task_id)
            except TaskHierarchy.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task not found.",
                })

            due_date = request.data.get('due_date')
            if due_date is not None:
                task.due_date = due_date
                user_instance = User.objects.get(id=user_id)
                TaskHierarchyAction.objects.create(
                    user_id=user_instance,
                    task=task,
                    remark="Task Due Date has been updated"
                )

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
            
            if 'assign_to' in request.data:
                if assign_to is None or assign_to == '':
                    task.assign_to.clear()
                else:
                    # Parse the provided user_ids and update assignees
                    assign_user_ids = [int(user_id) for user_id in assign_to.split(',') if user_id.strip()]
                    assign_users = User.objects.filter(id__in=assign_user_ids)
                    task.assign_to.set(assign_users)

            task.save()
            serializer = GetTaskHierarchySerializer(task)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task updated successfully.",
                "data": serializer.data
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update task.",
                "errors": str(e)
            })
            
    


    @csrf_exempt
    def delete_task(self,request):
        try:
            task_id = request.GET.get('task_id')
            user_id = request.GET.get('user_id')
            # task_hierarchy= TaskHierarchy.objects.all()
            # task_hierarchy.delete()
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "task deleted successfully",
            })
        except TaskHierarchy.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Board check not found",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to delete Board check",
                "errors": str(e)
            })
            
            
            

class TaskHierarchyChildrenViewSet(viewsets.ModelViewSet):
    @csrf_exempt
    def get_task_in_tasks(self, request):
        try:
            user_id = request.GET.get('user_id')
            task_id = request.GET.get('task_id')

            if not task_id:
                return JsonResponse({"success": False, "status": status.HTTP_400_BAD_REQUEST, "message": "Invalid request. task_id is missing."})

            def get_all_child_tasks(parent_id):
                children = TaskHierarchy.objects.filter(parent_id=parent_id, inTrash=False)
                result = set()
                for child in children:
                    result.add(child.id)
                    result.update(get_all_child_tasks(child.id))
                return result

            all_child_tasks = get_all_child_tasks(task_id)

            # Fetch all subtasks that are either assigned to or created by the user
            relevant_subtasks = TaskHierarchy.objects.filter(
                Q(assign_to=user_id) | Q(created_by=user_id),
                id__in=all_child_tasks,
                inTrash=False
            ).order_by('created_at').distinct()

            # Fetch immediate children of the given task
            immediate_children = TaskHierarchy.objects.filter(
                parent_id=task_id,
                inTrash=False
            ).order_by('created_at')

            relevant_immediate_children = []
            for child in immediate_children:
                if any(subtask.id in all_child_tasks for subtask in relevant_subtasks):
                    relevant_immediate_children.append(child)
            
            # Previous logic
            subtasks = TaskHierarchy.objects.filter(
                # Q(assign_to=user_id) | Q(created_by=user_id) | Q(parent__created_by=user_id) | Q(parent__assign_to=user_id),
                parent_id=task_id,
                inTrash=False
            ).order_by('created_at').distinct()

            if not subtasks.exists():
                task_ids = set()
                current_task_id = task_id
                while current_task_id:
                    parent_task = TaskHierarchy.objects.filter(id=current_task_id, inTrash=False).values('parent_id').first()
                    if parent_task and parent_task['parent_id']:
                        task_ids.add(parent_task['parent_id'])
                        current_task_id = parent_task['parent_id']
                    else:
                        break

                subtasks = TaskHierarchy.objects.filter(
                    Q(assign_to=user_id) | Q(created_by=user_id) | 
                    Q(checklist__board__assign_to=user_id) | Q(checklist__board__created_by=user_id),
                    Q(id__in=task_ids) | Q(parent_id=task_id),
                    inTrash=False
                ).order_by('created_at').distinct()
            
            
            # Prepare relevant_task_ids for serializer context
            relevant_task_ids = set(task.id for task in relevant_immediate_children)
            
            # Filter out only the adjacent children from the previous logic
            combined_tasks = set(relevant_immediate_children) | set(subtasks)
            
            serializer = TaskHierarchyChildrenSerializer(combined_tasks, many=True, context={'request': request, 'relevant_task_ids': relevant_task_ids})
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Subtasks retrieved successfully.",
                "data": {"subtasks": serializer.data}
            })

        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)


        
    @csrf_exempt
    def get_task_children(self, request):
        try:
            task_id = request.GET.get('task_id')

            if not task_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id is missing."
                })

            try:
                print("🐍 File: task_hierarchy/task.py | Line: 781 | get_task_children ~ task_id",task_id)
                task = TaskHierarchy.objects.get(id=task_id, inTrash=False)
                
                print("🐍 File: task_hierarchy/task.py | Line: 781 | get_task_children ~ task",task)
            except TaskHierarchy.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task not found."
                })

            children = TaskHierarchy.objects.filter(parent=task, inTrash=False).order_by('created_at')
            task_hierarchy = [self.build_task_hierarchy(child, 1) for child in children]

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Tasks retrieved successfully.",
                "data": {
                    "level_1": [task_hierarchy]
                }
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve tasks.",
                "errors": str(e)
            })
            
    def build_task_hierarchy(self, task, level):
        task_data = {
            "id": task.id,
            "task_topic": task.task_topic,
            "due_date": task.due_date,
            "task_level": task.task_level,
            "start_date":task.start_date,
            "end_date" :task.end_date,
            "status": {
                "id": task.status.id,
                "status_name": task.status.status_name,
                "color": task.status.color
            },
            "created_by": {
                "user_id": task.created_by.id,
                "email": task.created_by.email,
                "firstname": task.created_by.firstname,
                "lastname": task.created_by.lastname,
                "phone_no": task.created_by.phone_no
            },
            "assign_to": [{
                "user_id": user.id,
                "email":user.email,
                "firstname": task.created_by.firstname,
                "lastname": user.lastname,
                "phone_no": user.phone_no
                } 
                          for user in task.assign_to.all()],
            "parent": task.parent.id if task.parent else None,
            "depend_on": [{
            "task_id": dep_task.id,
            "task_topic": dep_task.task_topic 
        } for dep_task in task.depend_on.all()]
        }
        children = TaskHierarchy.objects.filter(parent=task, inTrash=False).order_by('created_at')
        if children.exists():
            task_data[f"level_{level + 1}"] = [self.build_task_hierarchy(child, level + 1) for child in children]
        return task_data


    @csrf_exempt
    def get_user_tasks_test(self, request):
        try:
            user_id = request.GET.get('user_id')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id is missing."
                })

            user_tasks = TaskHierarchy.objects.filter(
                Q(created_by_id=user_id) | Q(assign_to__id=user_id),
                parent__isnull=True,
                inTrash=False
            ).distinct().order_by('created_at')

            task_hierarchy = [self.build_task_hierarchy_test(task, 1) for task in user_tasks]

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Tasks retrieved successfully.",
                "data": {
                    "level_1": task_hierarchy
                }
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve tasks.",
                "errors": str(e)
            })


    def build_task_hierarchy_test(self, task, level):
        task_data = {
        "id": task.id,
        "task_topic": task.task_topic,
        "due_date": task.due_date,
        "task_level": task.task_level,
        "created_by": {
            "id": task.created_by.id,
            "username": task.created_by.firstname
        },
        "assign_to": [{"id": user.id, "username": user.firstname} for user in task.assign_to.all()],
        "parent": task.parent.id if task.parent else None,
        }
        children = TaskHierarchy.objects.filter(parent=task, inTrash=False).order_by('created_at')
        if children.exists():
            task_data[f"level_{level + 1}"] = [self.build_task_hierarchy_test(child, level + 1) for child in children]
        return task_data


class TaskHierarchyDependenciesViewSet(viewsets.ModelViewSet):
    
    def get_main_parent_id(self, task_id):
        try:
            task = TaskHierarchy.objects.get(id=task_id)
            main_task = task
            while main_task.parent is not None:
                main_task = main_task.parent
            
            if main_task.id == task_id:
                return None  # The given task is the main parent
            return main_task.id  # Return the main parent ID
        except TaskHierarchy.DoesNotExist:
            return None
        
    def get_all_parent_task_ids(self, child_task_id):
        """
        This function takes a child task ID and returns a list of all parent task IDs up to the main task.
        """
        def recursive_get_parents(task_id):
            try:
                task = TaskHierarchy.objects.get(id=task_id)
                parent_id = task.parent_id
                if parent_id:
                    parent_task = TaskHierarchy.objects.get(id=parent_id)
                    parent_ids.append(parent_task.id)
                    recursive_get_parents(parent_task.id)
            except TaskHierarchy.DoesNotExist:
                pass
    
        parent_ids = []
        recursive_get_parents(child_task_id)
        return parent_ids

    @csrf_exempt
    def get_dependent_tasks(self, request):
        task_id = request.GET.get('task_id')
        user_id = request.GET.get('user_id')
        
        if not task_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. task_id is missing.",
            })
        
        try:
            parent_task = TaskHierarchy.objects.get(id=task_id)
            dependent_tasks = parent_task.depend_on.all()
            
            data = []
            for task in dependent_tasks:
                data.append({
                    "task_id": task.id,
                    "task_topic": task.task_topic
                })
            
            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "data": data,
            }
            return JsonResponse(response)
        
        except TaskHierarchy.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Task not found.",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve dependent tasks.",
                "errors": str(e)
            })
            
   

    @csrf_exempt
    def get_tasks_for_dependencies(self, request):
        try:
            user_id = request.GET.get('user_id')
            subtask_id = request.GET.get('subtask_id')
            parent_id = request.GET.get('parent_id')
            board_id = request.GET.get('board_id')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Invalid request. user_id is missing."
                })

            task_data = []

            if parent_id and subtask_id:
                subtask = TaskHierarchy.objects.filter(
                    id=subtask_id,
                    inTrash=False
                ).first()
                parent_task = TaskHierarchy.objects.filter(
                    id=parent_id,
                    inTrash=False
                ).first()
                
                parent_ids = self.get_all_parent_task_ids(subtask.id)

                if subtask and parent_task:
                    task_data.extend(self.fetch_all_subtasks(parent_task.id, subtask.id, parent_ids))
                    task_data = [task for task in task_data if task['task_id'] not in parent_ids]

            elif parent_id:
                    ignore_task = TaskHierarchy.objects.filter(
                        id=parent_id,
                        due_date__isnull=False,
                        inTrash=False
                    ).first()
                    if board_id and board_id != "null":
                        tasks = TaskHierarchy.objects.filter(
                            # Q(assign_to=user_id) | Q(created_by=user_id),
                            parent__isnull=True,
                            due_date__isnull=False,
                            checklist__board=board_id,
                            inTrash=False
                        ).order_by('created_at').distinct()

                        if ignore_task:
                            tasks = tasks.exclude(id=ignore_task.id)
                    else:
                        tasks = TaskHierarchy.objects.filter(
                            Q(assign_to=user_id) | Q(created_by=user_id),
                            parent__isnull=True,
                            due_date__isnull=False,
                            checklist=None,
                            inTrash=False
                        ).order_by('created_at').distinct()

                        if ignore_task:
                            tasks = tasks.exclude(id=ignore_task.id)

                    for task in tasks:
                        task_data.append({"task_id": task.id, "task_topic": task.task_topic, "parent": task.parent_id})
            else:
                if board_id and board_id != "null":
                    tasks = TaskHierarchy.objects.filter(
                            parent__isnull=True,
                            due_date__isnull=False,
                            checklist__board=board_id,
                            inTrash=False
                        ).order_by('created_at').distinct()
                else:
                    tasks = TaskHierarchy.objects.filter(
                            Q(assign_to=user_id) | Q(created_by=user_id),
                            parent__isnull=True,
                            due_date__isnull=False,
                            checklist=None,
                            inTrash=False
                        ).order_by('created_at').distinct()
                
                for task in tasks:
                    task_data.append({"task_id": task.id, "task_topic": task.task_topic})
                    
            return JsonResponse({
                "success": True,
                "status": 200,
                "message": "Tasks fetched successfully.",
                "data": task_data
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": str(e)
            })
            
    def fetch_all_subtasks(self, parent_task_id, task_to_ignore,parent_ids):
        """
        This function takes a parent task ID and returns a list of all child tasks with their IDs and topics up to the last level.
        """
        def recursive_get_children(task):
            children = TaskHierarchy.objects.filter(parent=task).exclude(id__in=[task_to_ignore])
            
            # children = TaskHierarchy.objects.filter(parent=task)
            children_info = []
            for child in children:
                child_info = {
                    "task_id": child.id,
                    "task_topic": child.task_topic
                }
                children_info.append(child_info)
                children_info.extend(recursive_get_children(child))
            return children_info

        try:
            parent_task = TaskHierarchy.objects.get(id=parent_task_id)
            all_children_info = recursive_get_children(parent_task)
            return all_children_info
        except TaskHierarchy.DoesNotExist:
            return []


    # def fetch_all_subtasks(self, parent_task_id, task_to_ignore_id=None):
    #     children_tasks = TaskHierarchy.objects.filter(parent_id=parent_task_id)
        
    #     if task_to_ignore_id:
    #         children_tasks = children_tasks.exclude(id=task_to_ignore_id)
        
    #     data = [
    #         {
    #             "task_id": task.id,
    #             "task_topic": task.task_topic
    #         }
    #         for task in children_tasks
    #     ]
        
    #     return data
            
    # def fetch_all_subtasks(self, task_id, task_to_ignore = None):
    #     subtasks = TaskHierarchy.objects.filter(parent_id=task_id, inTrash=False)
    #     print("🐍 File: task_hierarchy/task.py | Line: 1153 | fetch_all_subtasks ~ subtasks",subtasks)
    #     if task_to_ignore:
    #         subtasks = subtasks.exclude(id=task_to_ignore.id)
    #     subtasks = subtasks.order_by('created_at')
    #     task_list = []
    #     for subtask in subtasks:
    #         task_list.append({"task_id": subtask.id, "task_topic": subtask.task_topic})
    #         task_list.extend(self.fetch_all_subtasks(subtask.id, task_to_ignore))  # Recursively add subtasks
    #     return task_list
    
    
    @csrf_exempt
    def update_dependencies(self, request):
        try:
            task_id = request.data.get('task_id')
            user_id = request.data.get('user_id')

            if not task_id or not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id and user_id are required."
                })

            try:
                task = TaskHierarchy.objects.get(id=task_id)
            except TaskHierarchy.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task not found.",
                })


            dependencies = request.data.get('depend_on')
            
            
            
            if dependencies is None or dependencies == '':
                # If no assignees provided, clear all assignees
                task.depend_on.clear()
            else:
                # Parse the provided user_ids and update assignees
                depend_on_task_ids = [int(task_id) for task_id in dependencies.split(',') if task_id.strip()]
           
                if task.id in depend_on_task_ids:
                    
                    return JsonResponse({
                        "success": True,
                        "status": 123,
                        "message": "A task cannot be dependent on itself.",
                    })
                depend_ids = TaskHierarchy.objects.filter(id__in=depend_on_task_ids)
                task.depend_on.set(depend_ids)

            task.save()
            # serializer = GetTaskHierarchySerializer(task)
            
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task updated successfully.",
                # "data": serializer.data
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update task.",
                "errors": str(e)
            })




class TaskHierarchyMyDayViewSet(viewsets.ModelViewSet):
    
    
    @csrf_exempt
    def get_myday_user_task(self, request):
        user_id = request.GET.get('user_id')
        
        if not user_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. user_id is missing."
            })

        current_time = datetime.now()
        due_date_end = current_time + timedelta(hours=24)
        
        opened_status_ids = get_status_ids_from_assigned_side(user_id)
        
        common_conditions = Q(created_by=user_id) | Q(assign_to=user_id)
        common_filters = {
            'status__id__in': opened_status_ids,
            'status__isnull': False,
            'is_personal': False,
            'inTrash': False
        }

        
        all_tasks = TaskHierarchy.objects.filter(
            common_conditions,
            Q(urgent_status=True) | 
            Q(due_date__lte=current_time) | 
            Q(due_date__gt=current_time, due_date__lte=due_date_end),
            **common_filters
        ).distinct().order_by('due_date')
 
        # Personal tasks
        personal_status_ids = list(PersonalStatus.objects.filter(
            fixed_state__in=['Pending', 'InProgress'],
            user_id=user_id
        ).order_by('order').values_list('id', flat=True))
        
        personal_tasks = PersonalTask.objects.filter(
            Q(status__id__in=personal_status_ids),
            Q(due_date__lte=due_date_end),
            user_id=user_id,
            status__isnull=False,
            inTrash=False
        ).distinct().order_by('due_date')
 
        task_serializer = MyDayTaskHierarchyGetSerializer(all_tasks, many=True)
        personal_task_serializer = GetPersonalTaskOnMyDaySerializer(personal_tasks, many=True)
   
        combined_tasks = task_serializer.data + personal_task_serializer.data
        unique_tasks = list({task['id']: task for task in combined_tasks}.values())
        
        
        try:
          for task in unique_tasks:
            
              task_hierarchy = TaskHierarchy.objects.get(id=task['id'])
              main_parent = task_hierarchy
              while main_parent.parent is not None:
                  main_parent = main_parent.parent
              task['main_parent'] = main_parent.id
        except Exception as e:
            pass
            
     
        total_count = TaskHierarchy.objects.filter(common_conditions, **common_filters, due_date__isnull=False).count()
        
        urgent_count = all_tasks.filter(urgent_status=True).count()
        reopened_count = all_tasks.filter(reopened_count__gt=0).count()
        
        status_counts = {
            "Total": {"count": total_count, "avg": 100},
            "Urgent": {"count": urgent_count, "avg": round((urgent_count / total_count) * 100, 2) if total_count > 0 else 0},
            "Reopened": {"count": reopened_count, "avg": round((reopened_count / total_count) * 100, 2) if total_count > 0 else 0}
        }
       
        task_statuses = self.get_task_set_by_status_name(user_id)
        for Status in task_statuses:
            status_count = all_tasks.filter(status=Status).count()
            status_counts[Status.status_name] = {
                "count": status_count,
                "avg": round((status_count / total_count) * 100, 2) if total_count > 0 else 0
            }
        
        status_counts_list = [{"status": k, "count": v["count"], "avg": v["avg"]} for k, v in status_counts.items()]
        status_urgent_list = [{"status": Status.status_name, "count": all_tasks.filter(status=Status, urgent_status=True).count()} for Status in task_statuses]
   
        for task in unique_tasks:
            checklist_id = task.get("checklist")
            if checklist_id:
                try:
                    task["board_id"] = Checklist.objects.get(id=checklist_id).board_id
                except Checklist.DoesNotExist:
                    pass
        
        response_data = {
            "tasks": unique_tasks,
            "counts": {
                "status_counts": status_counts_list,
                "urgent_counts": status_urgent_list
            }
        }
        
        response = {
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "User tasks retrieved successfully.",
            "data": response_data
        }
        
        return compress(response)

    def get_task_set_by_status_name(self, user_id):
        get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)
        task_statuses = TaskStatus.objects.filter(organization=get_org_id.organization_id).order_by('order')
        return task_statuses


class TaskHierarchyCustomBoardViewSet(viewsets.ModelViewSet):
    
    
    @csrf_exempt
    def get_boards(self, request):
        try:
            user_id = request.GET.get('user_id')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id is missing."
                })

            boards_created_by = list(Board.objects.filter(created_by=user_id))
            boards_assigned_to = list(Board.objects.filter(assign_to=user_id))
            task_boards = list(Board.objects.filter(checklist__taskhierarchy__assign_to=user_id))
           

            # Combine the lists and remove duplicates while preserving order
            combined_boards_dict = {board.id: board for board in (boards_created_by + boards_assigned_to + task_boards)}
            combined_boards = list(combined_boards_dict.values())

            fav_boards = FevBoard.objects.filter(user_id=user_id).values_list('board__id', flat=True)
            
            for board in combined_boards:
                board.favorite = board.id in fav_boards
        
        
        
            sorted_boards = sorted(combined_boards, key=lambda x: (not x.favorite, x.board_name.lower()))

            serializer = GetBoardsInHierarchySerializer(sorted_boards, many=True)
            data = serializer.data

            response_data = {
                "boards": [],
            }

            for board_data in data:
                board_id = board_data['id']

                get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)

                task_statuses = TaskStatus.objects.filter(organization=get_org_id.organization_id).order_by('order')
                
                tasks_count = []
                for Status in task_statuses:
                    status_name = Status.status_name.lower()
                    tasks = TaskHierarchy.objects.filter(
                        Q(created_by=user_id) | Q(assign_to=user_id),
                        inTrash=False,
                        checklist__board_id=board_id,
                        status=Status
                    )
                    tasks_count.append({
                        "status": status_name,
                        "count": tasks.count(),
                        "color": Status.color
                    })

                board_data["tasks_count"] = tasks_count
                response_data["boards"].append(board_data)

            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "User Boards retrieved successfully.",
                "data": response_data
            }

            return JsonResponse(response)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve user boards.",
                "errors": str(e)
            })

    @csrf_exempt
    def get_custom_board_data(self, request):
        try:
            board_id = request.GET.get('board_id')
            user_id = request.GET.get('user_id')

            if board_id:
                board = Board.objects.get(id=board_id)
                serializer = InTaskHierarchyBoardSerializers(board)

                checklist_data = []
                checklists = Checklist.objects.filter(board_id=board_id).order_by('sequence', 'created_at')
                for checklist in checklists:
                    sequence_ordering = Case(
                        When(sequence__regex=r'^\d+(\.\d+)?$', then=Cast('sequence', FloatField())),
                        When(sequence__regex=r'^\d+$', then=Cast('sequence', IntegerField())),
                        default=Value(0),
                        output_field=IntegerField()
                    )

                    # Filter tasks assigned to the user
                    assigned_tasks = TaskHierarchy.objects.filter(
                        inTrash=False,
                        assign_to=user_id
                    )

                    # Find the main parent tasks
                    main_tasks = []
                    temp_tasks = set()
                    for task in assigned_tasks:
                        main_task = task
                        while main_task.parent is not None:
                            main_task = main_task.parent
                        if main_task.checklist:
                            main_tasks.append(main_task)
                            temp_tasks.add(main_task)

                    tasklists_temp = TaskHierarchy.objects.filter(
                        id__in=[task.id for task in temp_tasks],
                        inTrash=False,
                        checklist_id=checklist.id
                    ).order_by(sequence_ordering, 'sequence')
                    

                    if user_id:
                        tasklists = TaskHierarchy.objects.filter(
                            Q(Q(checklist_id__board__assign_to=user_id)
                            | Q(checklist_id__board__created_by=user_id)
                            | Q(assign_to=user_id) | Q(created_by=user_id)) ,
                            checklist_id=checklist.id,
                            inTrash=False,
                        )

                    Combine = tasklists_temp | tasklists
                    tasklist_serializer = CustomBoardTaskHierarchyGetSerializer(Combine, many=True)
                    tasks_data = []
                    encountered_tasks = set()

                    for task in tasklist_serializer.data:
                        task_id = f"t_{task['id']}"

                        if task_id not in encountered_tasks:
                            tasks = TaskHierarchy.objects.get(id=task['id'],inTrash=False)

                            created_by_id = task["created_by"]
                            created_by_instance = User.objects.get(id=created_by_id)

                            created_by_data = {
                                "id": created_by_instance.id,
                                "email": created_by_instance.email,
                                "firstname": created_by_instance.firstname,
                                "lastname": created_by_instance.lastname,
                            }

                            status_id = tasks.status
                            
                            if status_id:
                                

                                status_info = {
                                    "id": status_id.id,
                                    "status_name": status_id.status_name,
                                    "color": status_id.color,
                                }
                            else:
                                # If status_id is None, handle it as follows:
                                
                                # Retrieve the user's organization ID based on the provided user_id
                                get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)
                                
                                # Get the first TaskStatus for the user's organization that has fixed_state as "Pending"
                                task_status = TaskStatus.objects.filter(organization=get_org_id.organization_id,fixed_state="Pending").order_by('order').first()
                                
                                # Set the status_info dictionary with the task status details from the organization
                                status_info = {
                                    "id": task_status.id,
                                    "status_name": task_status.status_name,
                                    "color": task_status.color,
                                }
                                
                                # Update the task's status to the task_status retrieved for the user's organization
                                tasks.status= task_status
                                tasks.save()
                            
                            progress_percentage, division = self.calculate_progress_and_division(tasks)

                            if task["due_date"]:
                                IST = pytz.timezone('Asia/Kolkata')

                                if isinstance(task["due_date"], str):
                                    due_date_utc = datetime.fromisoformat(task["due_date"]).astimezone(IST)

                                tasks_data.append({
                                    "id": task_id,
                                    "sequence": task["sequence"],
                                    "task_topic": task["task_topic"],
                                    "task_description": task["task_description"],
                                    "task_status": status_info,
                                    "urgent_status": task["urgent_status"],
                                    "task_due_date": due_date_utc.strftime('%Y-%m-%d %H:%M:%S%z'),
                                    "task_created_at": task["created_at"],
                                    "task_assign_to": task["assign_to"],
                                    "depend_on": task["depend_on"],
                                    "task_created_by": created_by_data,
                                    "progress_percentage": progress_percentage, 
                                    "division": division,
                                })
                            else:
                                tasks_data.append({
                                    "id": task_id,
                                    "sequence": task["sequence"],
                                    "task_topic": task["task_topic"],
                                    "task_description": task["task_description"],
                                    "task_status": status_info,
                                    "urgent_status": task["urgent_status"],
                                    "task_due_date": None,
                                    "task_created_at": task["created_at"],
                                    "task_assign_to": task["assign_to"],
                                    "depend_on": task["depend_on"],
                                    "task_created_by": created_by_data,
                                    "progress_percentage": progress_percentage,
                                    "division": division,
                                })
                            encountered_tasks.add(task_id)
                    checklist_data.append({
                        "id": f"c_{checklist.id}",
                        "title": checklist.name,
                        "tasks": tasks_data,
                        "sequence": checklist.sequence,
                    })

                response_data = []
                for checklist in checklist_data:
                    section = {
                        "id": checklist["id"],
                        "title": checklist["title"],
                        "tasks": checklist["tasks"],
                        "sequence": checklist["sequence"],
                    }
                    response_data.append(section)

                try:
                    board_view = UserFilters.objects.get(user=user_id).custom_board_view
                except Exception as e:
                    board_view = None

                saved = SavedCategory.objects.filter(user_id=user_id, board_id=board_id).first()
                if saved:
                    saved_template = SavedTemplates.objects.filter(category=saved).first()
                    saved_template_name = saved_template.template_name if saved_template else None

                    # Count checklists and tasks related to the board
                    board_checklist_count = Checklist.objects.filter(board_id=board_id).count()
                    board_task_count = TaskHierarchy.objects.filter(checklist__board_id=board_id).count()

                    # Count checklists and tasks in SavedTemplateChecklist and SavedTemplateTaskList
                    saved_checklist_count = SavedTemplateChecklist.objects.filter(template=saved_template).count()
                    saved_task_count = SavedTemplateTaskList.objects.filter(checklist__template=saved_template).count()

                    # Determine if the board is partially saved
                    partial_saved = not (board_checklist_count == saved_checklist_count and board_task_count == saved_task_count)
                else:
                    saved_template_name = None
                    partial_saved = False
                
                response = {
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Board details retrieved successfully",
                    "saved": bool(saved),
                    "template_name": saved_template_name,
                    "partial_saved": partial_saved,
                    "board": serializer.data,
                    "data": response_data,
                    "board_view": board_view,
                    
                }

                return JsonResponse(response)

        except Board.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Board not found",
            })
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def calculate_progress_and_division(self, task):
        SubTask = TaskHierarchy.objects.filter(parent=task, inTrash=False)
        total_duration_to_due_date = timedelta()
        for subtask_task in SubTask:
            due_date = subtask_task.due_date
            if due_date:
                now = timezone.localtime(timezone.now())
                duration_to_due_date = due_date - now
                total_duration_to_due_date += duration_to_due_date


        total_subtask_task = SubTask.count()
        closed_status_ids = get_status_ids_from_creater_side(task.created_by.id, True)
        completed_subtask_task = SubTask.filter(status__id__in=closed_status_ids)
        total_duration_completed = timedelta()

        for subtask_task in completed_subtask_task:
            due_date = subtask_task.due_date
            if due_date:
                now = timezone.localtime(timezone.now())
                duration_to_due_date = due_date - now
                total_duration_completed += duration_to_due_date

        progress_percentage = 100
        if total_duration_to_due_date.total_seconds() > 0:
            if task.status and task.status.id in closed_status_ids:
                pass
            else:
                progress_percentage = round((total_duration_completed.total_seconds() / total_duration_to_due_date.total_seconds()) * 100, 2)
        elif task.status and task.status.id in closed_status_ids:
            progress_percentage = 100
        else:
            progress_percentage = 0

        division = f"{completed_subtask_task.count()}/{total_subtask_task}"
        return max(progress_percentage, 0), division
    
    
    @csrf_exempt
    def add_selected_template_to_board(self, request):
        try:    
            board_id = request.data.get('board_id')
            template_id = request.data.get('template_id')
            user_id = request.data.get('user_id')
            from_saved_template = request.data.get('from_saved_template', False)
            board = Board.objects.get(id=board_id)
            if template_id:
                try:
                    if from_saved_template == False:
                        template = Template.objects.get(id=template_id)
                        board.template = template
                        board.save()
                        Checklist.objects.filter(board=board).delete()
                        TaskHierarchy.objects.filter(checklist__board=board).delete()
                        
                        template_checklists = TemplateChecklist.objects.filter(template=template)
                        for index, template_checklist in enumerate(template_checklists, start=5):
                        
                            checklist = Checklist.objects.create(
                                board=board,
                                name=template_checklist.name,
                                sequence=str(index)
                            )

                            
                            template_tasklists = TemplateTaskList.objects.filter(checklist=template_checklist)
                            for index, template_tasklist in enumerate(template_tasklists, start=5):
                                TaskHierarchy.objects.create(
                                    created_by=board.created_by,
                                    checklist=checklist,
                                    task_topic=template_tasklist.task_name,
                                    sequence=str(index)
                                )
                    else:
                        template = SavedTemplates.objects.get(id=template_id)
                        # board.template = template
                        # board.save()
                        Checklist.objects.filter(board=board).delete()
                        TaskHierarchy.objects.filter(checklist__board=board).delete()
                        
                        template_checklists = SavedTemplateChecklist.objects.filter(template=template)
                        for index, template_checklist in enumerate(template_checklists, start=5):
                        
                            checklist = Checklist.objects.create(
                                board=board,
                                name=template_checklist.name,
                                sequence=str(index)
                            )

                            
                            template_tasklists = SavedTemplateTaskList.objects.filter(checklist=template_checklist)
                            for index, template_tasklist in enumerate(template_tasklists, start=5):
                                TaskHierarchy.objects.create(
                                    created_by=board.created_by,
                                    checklist=checklist,
                                    task_topic=template_tasklist.task_name,
                                    sequence=str(index)
                                )
                    
                    # static_checklists = ['In Progress', 'Completed', 'Done']
                    # for static_checklist_name in static_checklists:
                    #     Checklist.objects.create(board=board, name=static_checklist_name)

                except SavedTemplates.DoesNotExist:
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": "Template not found",
                    })

            # serializer = BoardSerializer(board)
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Board updated successfully",
            })
        except Board.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Board not found",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update board",
                "errors": str(e)
            })
    

class TaskHierarchyTrashViewSet(viewsets.ModelViewSet):

    def get_all_children_task_ids(self, parent_task_id):
        """
        This function takes a parent task ID and returns a list of all child task IDs up to the last level.
        """
        def recursive_get_children(task):
            children = TaskHierarchy.objects.filter(parent=task)
            children_ids = []
            for child in children:
                children_ids.append(child.id)
                children_ids.extend(recursive_get_children(child))
            return children_ids

        try:
            parent_task = TaskHierarchy.objects.get(id=parent_task_id)
            all_children_ids = recursive_get_children(parent_task)
            return all_children_ids
        except TaskHierarchy.DoesNotExist:
            return []
        
    @csrf_exempt
    def delete_task_data(self, request):
        task_id = request.GET.get('task_id')
        user_id = request.GET.get('user_id')
        try:
            task = TaskHierarchy.objects.get(id=task_id,created_by_id=user_id)
        except TaskHierarchy.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Tasks not found",
            })
            
        # Update the parent task
        task.inTrash = True
        task.trashed_with = 'Manually'
        task.save()
        
        
        children_ids = self.get_all_children_task_ids(task.id)
        
        TaskHierarchy.objects.filter(id__in=children_ids).update(inTrash=True, trashed_with='Relatively_task')
              
        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "Tasks Trashed successfully",
        })  
    

    @csrf_exempt
    def get_trashed_task(self, request):
        
        try:
            user_id = request.GET.get('user_id')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id is missing."
                })

            tasks_created_by = TaskHierarchy.objects.filter(
                created_by=user_id,inTrash=True, trashed_with= "Manually").order_by('updated_at')

            
            
            combined_data = list(tasks_created_by) 
            combined_serializer = CombinedTaskHierarchySerializer(combined_data, many=True)

            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "User Trashed tasks retrieved successfully.",
                "data": combined_serializer.data
            }

            return compress(response)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve user tasks.",
                "errors": str(e)
            })
            

    @csrf_exempt
    def untrash_task_data(self, request):
        task_id = request.data.get('task_id','')
        
        user_id = request.data.get('user_id')
       
            
        task_ids_list = [int(id.strip()) for id in task_id.split(',')]
        
        tasks = TaskHierarchy.objects.filter(id__in=task_ids_list, created_by_id=user_id)
        
        if not tasks.exists():
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "No tasks found",
            })

        for task in tasks:
            children_ids = self.get_all_children_task_ids(task.id)

            task.inTrash = False
            task.trashed_with = None
            task.save()

            TaskHierarchy.objects.filter(id__in=children_ids, trashed_with='Relatively_task').update(inTrash=False, trashed_with=None)

        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "Tasks Untrashed successfully",
        })  

    
    @csrf_exempt
    def parmanant_delete_task(self, request):
        task_id = request.GET.get('task_id')

        user_id = request.GET.get('user_id')

        if  not user_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request.  user_id is missing.",
            })

        
        
        

        try:
          
            if task_id:
                task_ids = [int(tid) for tid in task_id.split(',')]
                tasks = TaskHierarchy.objects.filter(
                id__in=task_ids, created_by=user_id, inTrash=True
                )
                tasks.delete()
                
          
                    

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "deleted successfully",
            })

        except ObjectDoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Tasks not found",
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to delete tasks.",
                "errors": str(e),
            })

           
            
# because of this error "can not serialize 'TaskHierarchy' object"""
class CustomJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, TaskHierarchy):
            return {
                'id': obj.id,
                'task_topic': obj.task_topic,
                'due_date': obj.due_date,
                # Add more fields as needed
            }
class TaskHierarchyRequestViewSet(viewsets.ModelViewSet):

    
    def create_notification_request(self, user, task, due_request):
        post_save.disconnect(notification_handler, sender=Notification)
        
        notification_msg = f"{user.firstname} {user.lastname} has requested a due date change for the task '{task.task_topic}'"
        action_content_type = ContentType.objects.get_for_model(TaskHierarchyDueRequest)
        
        notification = Notification.objects.create(
            user_id=user,
            where_to="request",
            notification_msg=notification_msg,
            action_content_type=action_content_type,
            action_id=due_request.id,
        )
        
        notification.notification_to.add(task.created_by)
        
        post_save.connect(notification_handler, sender=Notification)
        post_save.send(sender=Notification, instance=notification, created=True)

    
    
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
            user = User.objects.get(id=user_id)

            # Get the task
            task_id = request.POST.get('task_id')
            if not task_id:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "task_id is required."
                })
            

           
            task = TaskHierarchy.objects.get(id=task_id)
            
            
            # Create the request
            due_request = TaskHierarchyDueRequest.objects.create(
                sender=user,
                receiver=task.created_by,
                task=task,
                current_due_date=task.due_date,
                proposed_due_date=request.POST.get('due_date')
            )
            timezone = pytz.timezone('Asia/Kolkata')

            # Format current due date without the timezone offset
            current_due_date_str = task.due_date.replace(tzinfo=pytz.utc).astimezone(timezone).strftime('%Y-%m-%d %H:%M:%S') if task.due_date else "None"

            # Format proposed due date without the timezone offset
            proposed_due_date_str = datetime.strptime(request.POST.get('due_date'), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')

            remark=f"Request to change due date for '{task.task_topic}' from {current_due_date_str} to {proposed_due_date_str}."

            TaskHierarchyAction.objects.create(
                                    user_id=user,
                                    task=task,
                                    remark=remark
                                )
            # Create notification
            self.create_notification_request(user, task, due_request)
            return JsonResponse({
            "success": True,
            "status": 201,
            "message": "Request created successfully."
        }, encoder=CustomJSONEncoder)

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": "User not found."
            })

        except TaskHierarchy.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": "Task not found."
            })

        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)

       
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


        task = TaskHierarchyDueRequest.objects.filter(receiver=user_instance, inTrash = False)
        
        serializer = GetDueDateRequestSerializer(task, many=True)

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

            if not all([request_id, status_value, user_id]):
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

            due_request = TaskHierarchyDueRequest.objects.filter(id=request_id, receiver=user_instance).first()
            if not due_request:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "DueRequest not found."
                })

            task = due_request.task 
            if not task:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task not found."
                })

            timezone = pytz.timezone('Asia/Kolkata')
            action_remark, due_date_remark, notification_msg = self.process_due_request_status(
                status_value, user_instance, due_request, task, timezone
            )

            TaskHierarchyAction.objects.create(
                user_id=user_instance,
                task=task,
                remark=f"Request to change due date for task '{task.task_topic}' has been {action_remark}.{due_date_remark}"
            )

            self.create_notification(user_instance, notification_msg, due_request)

            due_request.save()

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "errors": str(e),
            })

    def process_due_request_status(self, status_value, user_instance, due_request, task, timezone):
        if status_value == "1":  # "1" means "approved"
            due_request.status = "approved"
            task.due_date = due_request.proposed_due_date
            task.save()
            action_remark = "accepted"
            updated_due_date = task.due_date.replace(tzinfo=pytz.utc).astimezone(timezone).strftime('%Y-%m-%d %H:%M:%S')
            due_date_remark = f" The due date has been updated to {updated_due_date}."
            notification_msg = f"{user_instance.firstname} {user_instance.lastname} has approved your due date change request for the task '{task.task_topic}'"
        else:
            due_request.status = "rejected"
            action_remark = "rejected"
            due_date_remark = ""
            notification_msg = f"{user_instance.firstname} {user_instance.lastname} has rejected your due date change request for the task '{task.task_topic}'"
        
        return action_remark, due_date_remark, notification_msg

    def create_notification(self, user_instance, notification_msg, due_request):
        post_save.disconnect(notification_handler, sender=Notification)
        notification = Notification.objects.create(
            user_id=user_instance,
            where_to="request",
            notification_msg=notification_msg,
            action_content_type=ContentType.objects.get_for_model(TaskHierarchyDueRequest),
            action_id=due_request.id
        )
        notification.notification_to.add(due_request.sender)
        post_save.connect(notification_handler, sender=Notification)
        post_save.send(sender=Notification, instance=notification, created=True)


        
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
            due_request = TaskHierarchyDueRequest.objects.get(id=request_id, receiver=user_instance)
        except TaskHierarchyDueRequest.DoesNotExist:
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


class TaskHierarchyCommentViewSet(viewsets.ModelViewSet):

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

            task = TaskHierarchy.objects.filter(id=task_id).first()
            user = User.objects.filter(id=user_id).first()

            if not task or not user:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task or sender not found."
                })

            task_comment = TaskHierarchyComments(task=task, user_id=user, comment=comment)
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



            task_actions = TaskHierarchyComments.objects.filter(task_id=task_id).select_related('user_id').values(
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
            
    

class TaskHierarchyChatViewSet(viewsets.ModelViewSet):

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

            task = TaskHierarchy.objects.filter(id=task_id).first()
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
                task_chatting = TaskHierarchyChatting(task=task, sender=sender, message='employee/chat_files/'+message_upload.name)
            else:
                message_text = request.POST.get('message')
                # No file or image upload, only text message
                task_chatting = TaskHierarchyChatting(task=task, sender=sender, message=message_text)
            task_chatting.save()

         
            # Check if sender is in assign_to or created_by
            
            
                
            t = threading.Thread(target=self.send_notification_for_chat, args=(sender,task,"chat"))
            t.setDaemon(True) 
            t.start()

                
            chats = TaskHierarchyChatting.objects.filter(task=task)

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
    def get_task_chats_and_activities(self, request):
        try:
            task_id = request.GET.get('task_id')
            # user_id = request.GET.get('user_id')

            if not task_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id is missing."
                })

            task = TaskHierarchy.objects.filter(id=task_id).first()
            if not task:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task not found."
                })
            task_actions = TaskHierarchyAction.objects.filter(task_id=task_id).select_related('user_id').values(
                'task_id', 'created_at'
            ).annotate(username=Concat('user_id__firstname', Value(' '), 'user_id__lastname'), sender_id=F('user_id'),message=F('remark'))
            task_chats = TaskHierarchyChatting.objects.filter(task_id=task_id).values('task_id', 'sender_id', 'message', 'created_at').annotate(username=Concat('sender_id__firstname', Value(' '), 'sender_id__lastname'))
            
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

            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task chats retrieved successfully.",
                "data": merged_data
            }

            return JsonResponse(response)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve task chats.",
                "errors": str(e)
            })


    def send_notification_for_chat(self, sender, task, from_where):
        try:

            all_childrens = self.get_all_children_task_ids(task.id)
            task_hierarchy_users = TaskHierarchy.objects.filter(id__in=all_childrens).values_list('assign_to', 'created_by')
            # Collect all unique users
            user_ids = set()
            user_ids.update(task.assign_to.values_list('id', flat=True))
            user_ids.add(task.created_by.id)
            print("🐍 File: task_hierarchy/task.py | Line: 2163 | send_notification_for_chat ~ user_ids",user_ids)

            for hierarchy_user in task_hierarchy_users:
                user_ids.update(hierarchy_user)

            # Exclude the sender from the notification list
            user_ids.discard(sender.id)

            notification_msg = f"{sender.firstname} sent a new chat in task '{task.task_topic}'."
            post_save.disconnect(notification_handler, sender=Notification)

            notification = Notification.objects.create(
                user_id=sender,
                notification_msg=notification_msg,
                action_content_type=ContentType.objects.get_for_model(task),
                action_id=task.id,
                where_to="customboard" if task.checklist else "myboard"
            )
            print(user_ids)
            notification.notification_to.set(User.objects.filter(id__in=user_ids))

            post_save.connect(notification_handler, sender=Notification)
            post_save.send(sender=Notification, instance=notification, created=True)

        except Exception as e:
            print("Error in send_notification_for_chat:", str(e))
            
    
    def get_all_children_task_ids(self, parent_task_id):
        """
        This function takes a parent task ID and returns a list of all child task IDs up to the last level.
        """
        def recursive_get_children(task):
            children = TaskHierarchy.objects.filter(parent=task)
            children_ids = []
            for child in children:
                children_ids.append(child.id)
                children_ids.extend(recursive_get_children(child))
            return children_ids

        try:
            parent_task = TaskHierarchy.objects.get(id=parent_task_id)
            all_children_ids = recursive_get_children(parent_task)
            return all_children_ids
        except TaskHierarchy.DoesNotExist:
            return []
        

class TaskHierarchyCustomizeViewSet(viewsets.ModelViewSet):
    
    @csrf_exempt
    def get_meetings_and_tasks(self, request):
        try:
            user_id = request.GET.get('user_id')
            date_str = request.GET.get('date')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "User ID is required."
                })

            try:
                user_id = int(user_id)
            except ValueError:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Invalid User ID format."
                })

            if date_str:
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({
                        "success": False,
                        "status": 400,
                        "message": "Invalid date format. Use YYYY-MM-DD."
                    })

                meetings = Meettings.objects.filter(
                    Q(user_id=user_id) | Q(participant__id=user_id),
                    from_date=date
                ).distinct()
                tasks = TaskHierarchy.objects.filter(
                    Q(created_by_id=user_id) | Q(assign_to__id=user_id),
                    due_date__date=date
                ).distinct()
            else:
                meetings = Meettings.objects.filter(
                    Q(user_id=user_id) | Q(participant__id=user_id)
                ).distinct()
                tasks = TaskHierarchy.objects.filter(
                    Q(created_by_id=user_id) | Q(assign_to__id=user_id)
                ).distinct()

            
            task_and_meetings = list(meetings) + list(tasks)
            tasks_serializer = CombinedTaskMeetingSerializer(task_and_meetings, many=True)

            data =tasks_serializer.data

            return JsonResponse({
                "success": True,
                "status": 200,
                "message": "Data retrieved successfully.",
                "data": data
            })
        except Exception as e:
            return create_error_response(e, 500)

class SaveTemplateView(viewsets.ModelViewSet):
    
    # def save_template(self, request):
    #     try:
    #         user_id = request.data.get('user_id')
    #         template_ids = request.data.get('template')

    #         if not user_id or not template_ids:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": 400,
    #                 "message": "User ID, template IDs, and category ID are required."
    #             })

    #         try:
    #             user = User.objects.get(id=user_id)
    #         except User.DoesNotExist:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": 404,
    #                 "message": "User not found."
    #             })

      
    #         templates = Template.objects.filter(id=template_ids).first()
    #         if not templates:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": 404,
    #                 "message": "One or more templates not found."
    #             })

    #         saved_template, created = TestSavedTemplate.objects.get_or_create(
    #             user=user,
    #             category=templates.category
    #         )

    #         saved_template.template.add(templates)
    #         saved_template.save()


    #         return JsonResponse({
    #             "success": True,
    #             "status": 200,
    #             "message": "Template saved successfully." if created else "Template updated successfully."
    #             })
    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": 500,
    #             "message": "An error occurred.",
    #             "errors": str(e)
    #         })

    @csrf_exempt
    def save_template(self, request):
        if request.method != 'PUT':
            return JsonResponse({
                "success": False,
                "status": status.HTTP_405_METHOD_NOT_ALLOWED,
                "message": "Only PUT requests are allowed."
            })
        
        try:
            user_id = request.data.get('user_id')
            category_id = request.data.get('category_id')
            board_id = request.data.get('board_id')
            template_name = request.data.get('template_name')

            if not user_id or not board_id or not template_name:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "user_id, board_id, and template_name are required."
                })

            category_name = "No Name"
            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                    category_name = category.name
                except Category.DoesNotExist:
                    category_name = "No Name"
            
            try:
                board = Board.objects.get(id=board_id)
            except Board.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Board not found."
                })

            saved_category, created = SavedCategory.objects.get_or_create(
                user_id=user_id,
                board_id=board_id,
                name = category_name,
                defaults={ 'blank': False, 'created_at': timezone.now(), 'updated_at': timezone.now()}
            )

            if not created:
                saved_category.name = category_name
                saved_category.updated_at = timezone.now()
                saved_category.save()

            saved_template, created = SavedTemplates.objects.update_or_create(
                    category=saved_category,
                    defaults={'template_name': template_name, 'updated_at': timezone.now()}
                )

            if not created:
                saved_template.template_name = template_name
                saved_template.updated_at = timezone.now()
                saved_template.save()

            checklists = Checklist.objects.filter(board=board)
            for checklist in checklists:
                saved_checklist, created = SavedTemplateChecklist.objects.get_or_create(
                    template=saved_template,
                    name=checklist.name,
                    defaults={'created_at': timezone.now(), 'updated_at': timezone.now()}
                )

                if not created:
                    saved_checklist.updated_at = timezone.now()
                    saved_checklist.save()

                tasks = TaskHierarchy.objects.filter(checklist=checklist)
                for task in tasks:
                    saved_task, created = SavedTemplateTaskList.objects.get_or_create(
                        checklist=saved_checklist,
                        task_name=task.task_topic,
                        defaults={'created_at': timezone.now(), 'updated_at': timezone.now()}
                    )

                    if not created:
                        saved_task.updated_at = timezone.now()
                        saved_task.save()

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Template saved successfully."
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred.",
                "errors": str(e)
            })