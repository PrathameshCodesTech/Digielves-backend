import json
from configuration.gzipCompression import compress


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from digielves_setup.helpers.error_trace import create_error_response
from digielves_setup.models import Board, BoardPermission, Checklist, EmployeePersonalDetails, OutsiderUser, SubTaskChild, SubTasks, TaskHierarchy, TaskInBoardPermission, TaskSpecialAccess, TaskStatus, Tasks, User, UserFilters
from employee.views.controllers.status_controllers import get_status_ids_from_creater_side
from outsider.seriallizer.outsider_seriallizers import OutsiderBoardSerializers, OutsiderTaskSerializerForBoard, OutsiderTaskStatusSerializer, OutsiderUsersSerializer, OutsidersGetBoardsSerializer
from rest_framework import viewsets
from rest_framework import status
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.utils import timezone as newTimezone
from datetime import datetime, timedelta
from django.core.serializers import serialize
import pytz
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q

from django.db.models import Case, When, Value, IntegerField,FloatField
from django.db.models.functions import Cast
from django.utils import timezone
class OutsiderInEmployeeViewSets(viewsets.ModelViewSet):

    @csrf_exempt
    def get_outsiders(self, request):
        try:
            user_id = request.GET.get("user_id")
            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "user_id is required."
                })

            user = User.objects.get(id=user_id)
            outsiders = OutsiderUser.objects.filter(Q(added_by=user_id) | Q(secondary_adders__in=[user_id]))

            related_users = User.objects.filter(id__in=outsiders.values_list('related_id', flat=True), verified=1)

            serializer = OutsiderUsersSerializer(related_users, many=True)
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "data": serializer.data
            })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found."
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            })
    
    
    @csrf_exempt
    def give_access(self, request):
        try:
            user_id = request.POST.get('user_id')
            access_to = request.POST.get('access_to')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id is required."
                })

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "User not found."
                })

            if access_to is None or access_to.strip() == "":
                # If access_to is not provided or is empty, delete all existing access
                TaskSpecialAccess.objects.filter(user=user).delete()
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "All existing access removed successfully."
                })

            # Ensure access_to contains valid IDs
            access_to_ids = [id.strip() for id in access_to.split(',') if id.strip().isdigit()]
            if not access_to_ids:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid access_to IDs provided."
                })

            access_to_ids = [int(id) for id in access_to_ids]

            existing_access = TaskSpecialAccess.objects.filter(user=user)

            # Remove access that is not in the new list
            existing_access.exclude(access_to__id__in=access_to_ids).delete()

            for access_to_id in access_to_ids:
                try:
                    user_access = User.objects.get(id=access_to_id)
                    TaskSpecialAccess.objects.get_or_create(user=user, access_to=user_access)
                except User.DoesNotExist:
                    continue  # Skip if the user does not exist

            response = {
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Access granted successfully."
            }

            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "errors": str(e)
            })
            
    
    @csrf_exempt
    def get_accessed_task(self, request):

      
        user_id = request.GET.get('user_id')
        access_user_id = request.GET.get('access_user_id')

        if not user_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. user_id is missing."
            })
        userr = User.objects.get(id=user_id)

        tasks = TaskHierarchy.objects.filter(
            Q(created_by=user_id) | Q(assign_to=user_id),
            checklist__isnull=True, is_personal=False, inTrash=False, status__isnull=False
        ).distinct().order_by('due_date')
        
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
            
        get_org_id = EmployeePersonalDetails.objects.get(user_id=access_user_id)
        task_statuses = TaskStatus.objects.filter(organization=get_org_id.organization_id).order_by('order', 'created_at')

        fixed_state_titles_and_ids = [(Status.status_name,Status.fixed_state,Status.order ,Status.id) for Status in task_statuses]

        data = [
            {"id": f"s_{status_id}", "title": title,"fixed_state":fix_state,"order": order, "status_id": status_id, "tasks": []}
            for idx, (title,fix_state, order ,status_id) in enumerate(fixed_state_titles_and_ids)
        ]


  
        
        
        closed_status_ids = get_status_ids_from_creater_side(access_user_id, True)
        

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

        
        # try:
        #     board_view = UserFilters.objects.get(user=access_user_id).myboard_view
        # except Exception as e:
        #     board_view = None
        
        # users_with_access_gave = TaskSpecialAccess.objects.filter(user=userr).select_related('access_to')
        
        # access_list_gave = [
        #     {
        #         'user_id': access.access_to.id,
        #         'user_email': access.access_to.email,
        #         'access_type': access.access_type
        #     } for access in users_with_access_gave
        # ]
        
        response = {
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "User tasks retrieved successfully.",
            "access_board":True,
            "data": data,
            # "board_view":board_view
        }

        return JsonResponse(response, encoder=DateTimeEncoder)

        
        
    
    @csrf_exempt
    def get_outsider_task(self, request):

      
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
        
        
        outsiders = OutsiderUser.objects.filter(related_id=user_id)
        get_org_id = EmployeePersonalDetails.objects.get(user_id=outsiders.added_by)
        task_statuses = TaskStatus.objects.filter(organization=get_org_id.organization_id).order_by('order', 'created_at')

        fixed_state_titles_and_ids = [(Status.status_name,Status.fixed_state,Status.order ,Status.id) for Status in task_statuses]

        data = [
            {"id": f"s_{status_id}", "title": title,"fixed_state":fix_state,"order": order, "status_id": status_id, "tasks": []}
            for idx, (title,fix_state, order ,status_id) in enumerate(fixed_state_titles_and_ids)
        ]


  
        
        
        closed_status_ids = get_status_ids_from_creater_side(outsiders.added_by, True)
        

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

        
        # try:
        #     board_view = UserFilters.objects.get(user=access_user_id).myboard_view
        # except Exception as e:
        #     board_view = None
        
        # users_with_access_gave = TaskSpecialAccess.objects.filter(user=userr).select_related('access_to')
        
        # access_list_gave = [
        #     {
        #         'user_id': access.access_to.id,
        #         'user_email': access.access_to.email,
        #         'access_type': access.access_type
        #     } for access in users_with_access_gave
        # ]
        
        response = {
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "User tasks retrieved successfully.",
            "access_board":True,
            "data": data,
            # "board_view":board_view
        }

        return JsonResponse(response, encoder=DateTimeEncoder)
    
    
    
    
class DateTimeEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)



class OutsiderViewSets(viewsets.ModelViewSet):
    
    @csrf_exempt
    def get_accessed_task_new(self, request):

      
        user_id = request.GET.get('user_id')
        access_user_id = request.GET.get('access_user_id')

        if not user_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. user_id is missing."
            })
        userr = User.objects.get(id=user_id)

        tasks = TaskHierarchy.objects.filter(
            Q(created_by=user_id) | Q(assign_to=user_id),
            is_personal=False, inTrash=False, status__isnull=False
        ).distinct().order_by('due_date')
        
        main_tasks = set()

        # Add task IDs to the set
        for task in tasks:
            main_task = task
            while main_task.parent is not None:
                main_task = main_task.parent
            
            # if main_task.checklist is None: 
            main_tasks.add(main_task)
        all_tasks = {f"t_{task.id}" for task in main_tasks}
            
        try:
            outsiders = OutsiderUser.objects.get(related_id=user_id)
            org_details = EmployeePersonalDetails.objects.get(user_id=outsiders.added_by)
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
            
            progress_percentage, division = self.calculate_progress_and_division(task)
            
            task_data = {
                "id": task_id,
                "title": task.task_topic,
                "checklist": task.checklist.id if task.checklist else None,
                "description": task.task_description,
                "due_date": due_date_ist.strftime('%Y-%m-%d %H:%M:%S%z') if due_date_ist else None,
                "urgent_status": task.urgent_status,
                "status": task.status,
                "reopened_count": task.reopened_count,
                "created_at": task.created_at.isoformat(),
                "created_by": created_by_data,
                "assign_to": assign_to_data,
                "progress_percentage": progress_percentage,
                "division": division,
            }
            
            for idx, (title, fix_state, order, status_id) in enumerate(fixed_state_titles_and_ids):
                if task.status and task.status.id == status_id:
                    task_data["status"] = {
                        "id": task.status.id,
                        "status_name": task.status.status_name,
                        "color": task.status.color,
                    }
                    data[idx]["tasks"].append(task_data)
                    break

        for section in data:
            section["tasks"] = [task for task in section["tasks"] if task.get("due_date")]
            section["tasks"].sort(key=lambda task: task["due_date"])

  
        # ]
        
        response = {
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "User tasks retrieved successfully.",
            "access_board":True,
            "data": data,
            # "board_view":board_view
        }

        return JsonResponse(response, encoder=DateTimeEncoder)
    
    
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
    def get_outsider_task(self, request):

      
        user_id = request.GET.get('user_id')

        if not user_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. user_id is missing."
            })
        userr = User.objects.get(id=user_id)

        # tasks_created_by = Tasks.objects.filter(
        #     created_by=user_id,is_personal=False,inTrash=False).order_by('due_date')
        tasks_assigned_to = Tasks.objects.filter(
            assign_to=user_id, is_personal=False, inTrash=False).order_by('due_date')

        assigned_checklist_tasks = SubTasks.objects.filter(
            assign_to=user_id, due_date__isnull =False, inTrash=False).values_list('Task', flat=True).distinct()
        
        assigned_subtask_child = SubTaskChild.objects.filter(
            assign_to=user_id, due_date__isnull =False, inTrash=False).values_list('subtasks__Task', flat=True).distinct()
        
        parent_tasks = Tasks.objects.filter(
            id__in=assigned_checklist_tasks, inTrash=False).order_by('due_date')
        
        parent_tasks_child = Tasks.objects.filter(
            id__in=assigned_subtask_child, inTrash=False).order_by('due_date')
        

        all_tasks = set()

        # Add task IDs to the set
        # for task in tasks_created_by:
        #     all_tasks.add(f"t_{task.id}")
        for task in tasks_assigned_to:
            all_tasks.add(f"t_{task.id}")
        for parent_task in parent_tasks:
            all_tasks.add(f"t_{parent_task.id}")
        
        for parent_task_sub_child in parent_tasks_child:
            all_tasks.add(f"t_{parent_task_sub_child.id}")
        
        
        outsiders = OutsiderUser.objects.get(related_id=user_id)
        get_org_id = EmployeePersonalDetails.objects.get(user_id=outsiders.added_by)
        task_statuses = TaskStatus.objects.filter(organization=get_org_id.organization_id).order_by('order', 'created_at')

        fixed_state_titles_and_ids = [(Status.status_name,Status.fixed_state,Status.order ,Status.id) for Status in task_statuses]

        data = [
            {"id": f"s_{status_id}", "title": title,"fixed_state":fix_state,"order": order, "status_id": status_id, "tasks": []}
            for idx, (title,fix_state, order ,status_id) in enumerate(fixed_state_titles_and_ids)
        ]


  
        
        
        closed_status_ids = get_status_ids_from_creater_side(outsiders.added_by, True)
        

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
        
        # users_with_access_gave = TaskSpecialAccess.objects.filter(user=userr).select_related('access_to')
        
        # access_list_gave = [
        #     {
        #         'user_id': access.access_to.id,
        #         'user_email': access.access_to.email,
        #         'access_type': access.access_type
        #     } for access in users_with_access_gave
        # ]
        
        response = {
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "User tasks retrieved successfully.",
            "data": data,
            "board_view":board_view
        }

        return JsonResponse(response, encoder=DateTimeEncoder)


class OutsiderCustomBoardViewSets(viewsets.ModelViewSet):
    
    @csrf_exempt
    def get_outsider_boards(self, request):
        print("---------------------ajaja")
        try:
            user_id = request.GET.get('user_id')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id is missing."
                })


            permission_boards = list(Board.objects.filter(boardpermission__access_to=user_id))
            task_boards_permission = list(Board.objects.filter(taskinboardpermission__access_to=user_id))

            combined_boards_dict = {board.id: board for board in ( permission_boards + task_boards_permission)}
            combined_boards = list(combined_boards_dict.values())

            sorted_boards = sorted(combined_boards, key=lambda x: x.board_name.lower())

            serializer = OutsidersGetBoardsSerializer(sorted_boards, many=True)
            data = serializer.data

            response_data = {
                "boards": [],
            }

            for board_data in data:
                board_id = board_data['id']
                outsiders = OutsiderUser.objects.get(related_id=user_id)
                get_org_id = EmployeePersonalDetails.objects.get(user_id=outsiders.added_by)

                task_statuses = TaskStatus.objects.filter(organization=get_org_id.organization_id).order_by('order')

                # Check board permission for the user
                board_permission = BoardPermission.objects.filter(
                    board_id=board_id,
                    access_to=user_id
                ).first()
                
                task_in_board_permission = TaskInBoardPermission.objects.filter(board_id=board_id,
                    access_to=user_id).first()

                tasks_count = []

                for Status in task_statuses:
                    status_name = Status.status_name.lower()  # Convert to lowercase for consistent comparison
                    
                    if board_permission and board_permission.can_view_board and not board_permission.checklist_permissions.exists():
                        # User has access to the board but not specific checklists, show all tasks for the board
                        tasks = TaskHierarchy.objects.filter(
                            inTrash=False,
                            checklist__board_id=board_id,
                            status=Status
                        )
                    elif board_permission and board_permission.can_view_checklists:
                        
                            permitted_checklist_ids = board_permission.checklist_permissions.values_list('id', flat=True)
                            
                            tasks = TaskHierarchy.objects.filter(
                            inTrash=False,
                            checklist__board_id=board_id,
                            checklist_id__in=permitted_checklist_ids,
                            status=Status
                            )
                    elif task_in_board_permission:
                        tasks = TaskHierarchy.objects.filter(
                            inTrash=False,
                            checklist__board_id=board_id,
                            assign_to__in=[task_in_board_permission.user.id],
                            status=Status
                        )
                        

                    tasks_count.append({
                        "status": status_name,
                        "count": tasks.count(),
                        "color": Status.color  # Include status color
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
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @csrf_exempt
    def get_customboard_data(self, request):
        try:
            board_id = request.GET.get('board_id')
            user_id = request.GET.get('user_id')
            
            if not all([board_id, user_id]):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. board_id, user_id are required."
                })
            can_view_checklists = False 
            access_id = None
            try:
                board_permission = BoardPermission.objects.get(board_id=board_id, access_to=user_id)
                can_view_checklists = board_permission.can_view_checklists
                access_id=board_permission.user
            except BoardPermission.DoesNotExist:
                try:
                    task_board_permission = TaskInBoardPermission.objects.get(board_id=board_id, access_to=user_id)
                    can_view_checklists = False 
                    access_id = task_board_permission.user
                except TaskInBoardPermission.DoesNotExist:
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_403_FORBIDDEN,
                        "message": "User does not have access to this board."
                    })

            if board_id:
                board = Board.objects.get(id=board_id)
                serializer = OutsiderBoardSerializers(board)
 
                checklist_data = []
                
                if can_view_checklists:
                    allowed_checklists = board_permission.checklist_permissions.all()
                    checklists = Checklist.objects.filter(id__in=allowed_checklists, board_id=board_id).order_by('sequence', 'created_at')
                else:
                    checklists = Checklist.objects.filter(board_id=board_id).order_by('sequence', 'created_at')
                for checklist in checklists:
                    sequence_ordering = Case(
                    When(sequence__regex=r'^\d+(\.\d+)?$', then=Cast('sequence', FloatField())),
                    When(sequence__regex=r'^\d+$', then=Cast('sequence', IntegerField())),
                    default=Value(0),
                    output_field=IntegerField()
                    
                )
         
                    assigned_tasks = TaskHierarchy.objects.filter(
                        inTrash=False,
                        
                    # id__in=parent_tasks.values_list('id', flat=True),
                    checklist_id=checklist.id
                    ).order_by(sequence_ordering, 'sequence')
                    
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
                        checklist_id=checklist.id
                    ).order_by(sequence_ordering, 'sequence')
                    
                    if access_id:
                        assigned_tasks = assigned_tasks.filter( 
                                                     Q(Q(checklist_id__board__assign_to=access_id) 
                                                       | Q(checklist_id__board__created_by=access_id) 
                                                       | Q(assign_to = access_id),
                                                        checklist_id=checklist.id
                        
                                                       ))
                        
                        
                    Combine = tasklists_temp | assigned_tasks
                    tasklist_serializer = OutsiderTaskSerializerForBoard(Combine, many=True)
                    tasks_data = []
                    encountered_tasks = set()  # To keep track of encountered task IDs

 
                    
                    for task in tasklist_serializer.data:
                        task_id = f"t_{task['id']}"

                        if task_id not in encountered_tasks:
                            tasks = TaskHierarchy.objects.get(id=task['id'])
   
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
                                
                                get_org_id = EmployeePersonalDetails.objects.get(user_id=access_id)
                                
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
                        "sequence": checklist["sequence"],  # Include the sequence in the response
                    }
                    response_data.append(section)
                
             

                response = {
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Board details retrieved successfully",
                    "board": serializer.data,
                    "data": response_data
                    }

                return compress(response)
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
                "message": "Failed to retrieve board details",
                "errors": str(e)
            })
    
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
    
    
            
    # old
    # @csrf_exempt
    # def get_customboard_data(self, request):
    #     try:
    #         board_id = request.GET.get('board_id')
    #         user_id = request.GET.get('user_id')
            
    #         if not all([board_id, user_id]):
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": status.HTTP_400_BAD_REQUEST,
    #                 "message": "Invalid request. board_id, user_id are required."
    #             })
    #         can_view_checklists = False 
    #         access_id = None
    #         try:
    #             board_permission = BoardPermission.objects.get(board_id=board_id, access_to=user_id)
    #             can_view_checklists = board_permission.can_view_checklists
    #             access_id=board_permission.user
    #         except BoardPermission.DoesNotExist:
    #             try:
    #                 task_board_permission = TaskInBoardPermission.objects.get(board_id=board_id, access_to=user_id)
    #                 can_view_checklists = False 
    #                 access_id = task_board_permission.user
    #             except TaskInBoardPermission.DoesNotExist:
    #                 return JsonResponse({
    #                     "success": False,
    #                     "status": status.HTTP_403_FORBIDDEN,
    #                     "message": "User does not have access to this board."
    #                 })

    #         if board_id:
    #             board = Board.objects.get(id=board_id)
    #             serializer = OutsiderBoardSerializers(board)
 
    #             checklist_data = []
                
    #             if can_view_checklists:
    #                 allowed_checklists = board_permission.checklist_permissions.all()
    #                 checklists = Checklist.objects.filter(id__in=allowed_checklists, board_id=board_id).order_by('sequence', 'created_at')
    #             else:
    #                 checklists = Checklist.objects.filter(board_id=board_id).order_by('sequence', 'created_at')
    #             for checklist in checklists:
    #                 sequence_ordering = Case(
    #                 When(sequence__regex=r'^\d+(\.\d+)?$', then=Cast('sequence', FloatField())),
    #                 When(sequence__regex=r'^\d+$', then=Cast('sequence', IntegerField())),
    #                 default=Value(0),
    #                 output_field=IntegerField()
                    
    #             )
    #                 assigned_checklist_tasks = SubTasks.objects.filter(
    #                 assign_to=access_id).values_list('Task', flat=True).distinct()
                    
    #                 tasklists = Tasks.objects.filter(
    #                     inTrash=False,
    #                 # id__in=parent_tasks.values_list('id', flat=True),
    #                 checklist_id=checklist.id
    #                 ).order_by(sequence_ordering, 'sequence')
                    
    #                 if access_id:
    #                     tasklists = tasklists.filter( 
    #                                                  Q(Q(checklist_id__board__assign_to=access_id) 
    #                                                    | Q(checklist_id__board__created_by=access_id) 
    #                                                    | Q(assign_to = access_id) 
    #                                                    | Q(subtasks__assign_to=access_id)
    #                                                    | Q(subtasks__subtaskchild__assign_to=access_id)))
                        
                        

    #                 tasklist_serializer = OutsiderTaskSerializerForBoard(tasklists, many=True)
    #                 tasks_data = []
    #                 encountered_tasks = set()  # To keep track of encountered task IDs

 
                    
    #                 closed_status_ids = get_status_ids_from_creater_side(access_id, True)
    #                 for task in tasklist_serializer.data:
    #                     task_id = f"t_{task['id']}"

    #                     if task_id not in encountered_tasks:
    #                         tasks = Tasks.objects.get(id=task['id'])
   
    #                         Checklisttask = SubTasks.objects.filter(Task=task['id'], inTrash= False, due_date__isnull =False)
                            
    #                         total_duration_to_due_date = timedelta()
                            
    #                         for checklist_task in Checklisttask:
    #                             due_date = checklist_task.due_date
    #                             if due_date:
    #                                 now = newTimezone.localtime(newTimezone.now())
    #                                 duration_to_due_date = due_date - now
                
    #                                 total_duration_to_due_date += duration_to_due_date
                            
                            
                             
    #                         total_checklist_task = Checklisttask.count()
                            
                            
    #                         completed_checklist_task = Checklisttask.filter(status__id__in=closed_status_ids)
    #                         # Initialize total duration of completed checklist tasks
    #                         total_duration_completed = timedelta()
                            
    #                         # Calculate the total duration of completed checklist tasks
    #                         for checklist_task in completed_checklist_task:
                             
    #                             due_date = checklist_task.due_date
    #                             if due_date:
    #                                 now = newTimezone.localtime(newTimezone.now())
    #                                 duration_to_due_date = due_date - now
    #                                 total_duration_completed += duration_to_due_date
                            
                      
    #                         progress_percentage = 100
     
    #                         if total_duration_to_due_date.total_seconds() > 0:
                                
    #                             if task["status"]  in closed_status_ids:
    #                                 pass
    #                             else:
    #                                 # progress_percentage = round((completed_checklist_task / total_checklist_task) * 100 ,2)
    #                                 progress_percentage = round((total_duration_completed.total_seconds() / total_duration_to_due_date.total_seconds()) * 100, 2)                    
    #                         elif task["status"] in closed_status_ids:
                                
    #                             progress_percentage =  100
                            
    #                         else:
    #                             progress_percentage =  0

                           
                            
    #                         created_by_id = task["created_by"]
    #                         created_by_instance = User.objects.get(id=created_by_id)
                            
    #                         created_by_data = {
    #                             "id": created_by_instance.id,
    #                             "email": created_by_instance.email,
    #                             "firstname": created_by_instance.firstname,
    #                             "lastname": created_by_instance.lastname,
    #                         }
                            
                            
    #                         status_id = tasks.status
    #                         if status_id:
    #                             # If status_id is not None, set the status_info dictionary with the provided status details
    #                             status_info = {
    #                                 "id": status_id.id,
    #                                 "status_name": status_id.status_name,
    #                                 "color": status_id.color,
    #                             }  
    #                         else:
    #                             # If status_id is None, handle it as follows:
                                
    #                             # Retrieve the user's organization ID based on the provided user_id
    #                             get_org_id = EmployeePersonalDetails.objects.get(user_id=access_id)
                                
    #                             # Get the first TaskStatus for the user's organization that has fixed_state as "Pending"
    #                             task_status = TaskStatus.objects.filter(organization=get_org_id.organization_id,fixed_state="Pending").order_by('order').first()
                                
    #                             # Set the status_info dictionary with the task status details from the organization
    #                             status_info = {
    #                                 "id": task_status.id,
    #                                 "status_name": task_status.status_name,
    #                                 "color": task_status.color,
    #                             }
                                
    #                             # Update the task's status to the task_status retrieved for the user's organization
    #                             tasks.status= task_status
    #                             tasks.save()
                                
    #                         if task["due_date"]:
    #                             IST = pytz.timezone('Asia/Kolkata')
                
    #                             # due_date_ist = task["due_date"].astimezone(IST)
    #                             if isinstance(task["due_date"], str):
    #                                 # Convert string to datetime object
    #                                 due_date_utc = datetime.fromisoformat(task["due_date"]).astimezone(IST)
                                
                                    
    #                             tasks_data.append({
    #                                 "id": task_id,
    #                                 "sequence": task["sequence"],
    #                                 "task_topic": task["task_topic"],
    #                                 "task_description": task["task_description"],
    #                                 "task_status": status_info,
    #                                 "urgent_status":task["urgent_status"],
    #                                 "task_due_date": due_date_utc.strftime('%Y-%m-%d %H:%M:%S%z'),
    #                                 "task_created_at": task["created_at"],
    #                                 "task_assign_to": task["assign_to"],
    #                                 "task_created_by": created_by_data,
    #                                 "progress_percentage": max(progress_percentage, 0),
    #                                 "division": f"{completed_checklist_task.count()}/{total_checklist_task}"
    #                             })
    #                         else:
    #                             tasks_data.append({
    #                                 "id": task_id,
    #                                 "sequence": task["sequence"],
    #                                 "task_topic": task["task_topic"],
    #                                 "task_description": task["task_description"],
    #                                 "task_status": status_info,
    #                                 "urgent_status":task["urgent_status"],
    #                                 "task_due_date": None,
    #                                 "task_created_at": task["created_at"],
    #                                 "task_assign_to": task["assign_to"],
    #                                 "task_created_by": created_by_data,
    #                                 "progress_percentage": max(progress_percentage, 0),
    #                                 "division": f"{completed_checklist_task.count()}/{total_checklist_task}"
    #                             })
    #                         encountered_tasks.add(task_id)
    #                 checklist_data.append({
    #                     "id": f"c_{checklist.id}",
    #                     "title": checklist.name,    
    #                     "tasks": tasks_data,
    #                     "sequence": checklist.sequence,
    #                 })

    #             response_data = []
    #             for checklist in checklist_data:
                    
    #                 section = {
    #                     "id": checklist["id"],
    #                     "title": checklist["title"],
    #                     "tasks": checklist["tasks"],
    #                     "sequence": checklist["sequence"],  # Include the sequence in the response
    #                 }
    #                 response_data.append(section)
                
             

    #             response = {
    #                 "success": True,
    #                 "status": status.HTTP_200_OK,
    #                 "message": "Board details retrieved successfully",
    #                 "board": serializer.data,
    #                 "data": response_data
    #                 }

    #             return compress(response)
    #     except Board.DoesNotExist:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_404_NOT_FOUND,
    #             "message": "Board not found",
    #         })
    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "Failed to retrieve board details",
    #             "errors": str(e)
    #         })
            
            

    @csrf_exempt
    def get_task_status(self, request):
        try:
            user_id = request.GET.get('user_id')
            
            outsiders = OutsiderUser.objects.get(related_id=user_id)
            get_org_id = EmployeePersonalDetails.objects.get(user_id=outsiders.added_by)



            fixed_state_mapping = {
            "Pending": "Pending",
            "InProgress": "InProgress",
            "OnHold" : "OnHold"
            }
    
            if True:
                fixed_state_mapping["Completed"] = "Completed"

            fixed_states_to_include = list(fixed_state_mapping.values())
           

            fixed_state_ids = TaskStatus.objects.filter(
                    fixed_state__in=fixed_states_to_include,
                    organization=get_org_id.organization_id
                ).order_by('order')
 
            status_serializer = OutsiderTaskStatusSerializer(fixed_state_ids, many=True)

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
        
        