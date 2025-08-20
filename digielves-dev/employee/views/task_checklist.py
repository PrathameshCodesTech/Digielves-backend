from django.http import JsonResponse
from digielves_setup.models import SubTasks, EmployeePersonalDetails, TaskChecklist, TaskStatus, Tasks, User
from employee.seriallizers.task_seriallizers import GetChecklistTasksSerializer, GetTaskChecklistSerializer, GetTaskChecklistsSerializer, TaskChecklistSerializer
from rest_framework import status
from rest_framework.decorators import api_view

from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from django.core.serializers import serialize
from django.db.models import Q
from django.db.models import Count
class TaskChecklistViewSet(viewsets.ModelViewSet):
    serializer_class = TaskChecklistSerializer


    @csrf_exempt
    def create_task_checklist(self,request):
        
        serializer = TaskChecklistSerializer(data=request.data)

        try:
            if serializer.is_valid():
                task_checklist = serializer.save()


                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Task Checklists created successfully.",
                    "data": serializer.data
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create Task Checklist.",
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
    def GetTasksChecklists(self, request):
        
        task_id = request.GET.get('task_id')
        user_id = request.GET.get('user_id')

        if not task_id or not user_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. Both task_id and user_id are required."
            })

        try:
            task = Tasks.objects.get(id=task_id)
            
            print("----------------------------jajaajajajaaj")
            print(str(user_id) == str(task.created_by.id))
            if str(user_id) == str(task.created_by.id):
                
                task_checklists = TaskChecklist.objects.filter(
                Task=task,status__isnull=False,inTrash=False
                ).distinct().order_by('created_at')
            else:

                task_checklists = TaskChecklist.objects.filter(
                    Q(created_by=user_id) | Q(subtasks__assign_to=user_id),
                    Task=task,status__isnull=False,inTrash=False
                ).distinct().order_by('created_at')
            
            
            print(task_checklists)

            checklist_serializer = GetTaskChecklistSerializer(task_checklists, many=True)

            data = {"checklist": []}

            for checklist in task_checklists:
                checklist_serializer = GetTaskChecklistSerializer(checklist)
                checklist_data = checklist_serializer.data

              
                checklist_tasks = SubTasks.objects.filter(
                    Q(task_checklist__Task__created_by=user_id)|Q(created_by=user_id) | Q(assign_to=user_id) ,status__isnull=False,
                    task_checklist=checklist, inTrash=False
                ).distinct().order_by('created_at')

                checklist_tasks_serializer = GetChecklistTasksSerializer(checklist_tasks, many=True)
                checklist_data["checklist_tasks"] = checklist_tasks_serializer.data

                data["checklist"].append(checklist_data)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task data retrieved successfully.",
                "data": data
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
                "message": "Failed to retrieve task data.",
                "errors": str(e)
            })
            
    
    @csrf_exempt
    def GetTaskChecklists(self, request):
        
        task_id = request.GET.get('task_id')
        user_id = request.GET.get('user_id')

        if not task_id or not user_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. Both task_id and user_id are required."
            })

        try:
            task = Tasks.objects.get(id=task_id)
            
            task_checklist = TaskChecklist.objects.filter(Task= task, inTrash = False)

            checklist_serializer = GetTaskChecklistsSerializer(task_checklist, many=True)


            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task Checklist retrieved successfully.",
                "data": checklist_serializer.data
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
                "message": "Failed to retrieve task checklist.",
                "errors": str(e)
            })
    
    


    @csrf_exempt
    def updatTaskChecklist(self, request):
        try:
            check_id = request.data.get('check_id')
            user_id = request.data.get('user_id')

            if not (check_id and user_id):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. check_id and user_id are required."
                })
            
            try:

                check = TaskChecklist.objects.get(
                    Q(created_by=user_id) | Q(Task__created_by=user_id),id=check_id)
            except TaskChecklist.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": "You don't have permission to update this checklist."
                })
                
            
            new_status = request.data.get('status')
            got_task_statu = TaskStatus.objects.get(id=new_status)
            get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)
            not_this_fixed_status = {
                    "Closed": "Closed",
                    "Client Action Pending": "Client Action Pending",
                    "InReview" : "InReview"
                }
            not_this_fixed_states = not_this_fixed_status.values()

            not_this_task_statuses = TaskStatus.objects.filter(fixed_state__in=not_this_fixed_states,organization=get_org_id.organization_id)
            not_fixed_state_ids = [Status.id for Status in not_this_task_statuses]
            
            checkTask=len(SubTasks.objects.filter(task_checklist=check))
            checkTask_with_status = len(SubTasks.objects.filter(task_checklist=check,status=got_task_statu).distinct())
            
            int_status = int(new_status)
            if checkTask==checkTask_with_status or int_status not in not_fixed_state_ids:
                if new_status:
                    check.status = got_task_statu
                    check.save()

                    response = {
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "has_to_show":False,
                        "message": "Task updated successfully."
                    }
                else:
                    response = {
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Missing 'status' parameter in the request."
                    }
            else:
                
                response = {
                    "success": False,
                    "has_to_show":True,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Cannot update status. Checklist Tasks have different statuses."
                }

            return JsonResponse(response)

        except TaskChecklist.DoesNotExist:
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
    def updateChecklistFields(self, request):
        try:
            check_id = request.data.get('checklist_id')
            user_id = request.data.get('user_id')

            print(check_id)
            if not (check_id and user_id):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id and user_id are required."
                })

            check = TaskChecklist.objects.get(id=check_id)
 
            
            
            name = request.data.get('name')
            if name is not None:
                check.name = name
            
            completeded = request.data.get('completed')
            if completeded is not None:
                if completeded == "true":
                    check.completed = True
                elif completeded == "false":
                    check.completed = False
                else:
                    check.completed= completeded
                check.save()
            # from this 
            due_date = request.data.get('due_date')
            if due_date is not None:
                check.due_date = due_date

            urgent_status = request.data.get('urgent_status')
            if urgent_status is not None:
                check.urgent_status = urgent_status
                
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
                check.assign_to.set(assign_users)
            # to this has to delete
            
            check.save()



            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Checklist updated successfully."
            }

            return JsonResponse(response)

        except TaskChecklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Checklist not found.",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update checklist.",
                "errors": str(e)
            })
    
    @csrf_exempt
    def delete_checklistData(self, request):
        check_id = request.GET.get('checklist_id')
        user_id = request.GET.get('user_id')
        
        
        try:
            
            check = TaskChecklist.objects.get(id=check_id, created_by=user_id)
        except TaskChecklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": "You don't have permission to delete this checklist",
            })

        try:
            check = TaskChecklist.objects.get(id=check_id)
        except TaskChecklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "checklist not found",
            })
        check.delete()
        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "Checklist deleted successfully",
        })  
    
    @csrf_exempt
    def moveToTrash(self, request):
        check_id = request.GET.get('checklist_id')
        user_id = request.GET.get('user_id')
        
        
        try:
            

            check = TaskChecklist.objects.get(
                 Q(created_by=user_id) | Q(Task__created_by=user_id),
                    id=check_id,
                )
        except TaskChecklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": "You don't have permission to delete this checklist",
            })

        try:
            check = TaskChecklist.objects.get(id=check_id)
            check.inTrash = True
            check.trashed_with="Manually"
            check.save()
            
            SubTasks.objects.filter(task_checklist = check.id).update(inTrash=True,trashed_with="Relatively_checklist")
            
            
        except TaskChecklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "checklist not found",
            })

        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "Checklist moved successfully",
        }) 
    
    