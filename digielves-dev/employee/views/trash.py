from django.http import JsonResponse

from configuration.gzipCompression import compress
from digielves_setup.models import SubTasks, TaskChecklist, Tasks
from employee.seriallizers.trash_seriallizer import CombinedTaskTaskChecklistChecklistTaskSerializerOnly, GetTrashedTasksSerializer
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

class TasksTrashViewSet(viewsets.ModelViewSet):

    

    @csrf_exempt
    def getTrashed_task(self, request):
        
        try:
            user_id = request.GET.get('user_id')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id is missing."
                })

            tasks_created_by = Tasks.objects.filter(
                created_by=user_id,inTrash=True).order_by('updated_at')

            taskchecklist_created_by = TaskChecklist.objects.filter(
                created_by=user_id,inTrash=True,Task__inTrash=False).order_by('updated_at')
            
            checklistTask_created_by = SubTasks.objects.filter(
                created_by=user_id,inTrash=True,Task__inTrash=False).order_by('updated_at')
            
            
            combined_data = list(tasks_created_by) + list(taskchecklist_created_by)+ list(checklistTask_created_by)
            combined_serializer = CombinedTaskTaskChecklistChecklistTaskSerializerOnly(combined_data, many=True)

            
            


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
    def Update_to_unTrash(self, request):
        try:
            task_id = request.data.get('task_id')
            task_checklist = request.data.get('task_checklist')
            checklist_tasks = request.data.get('checklist_tasks')
            user_id = request.data.get('user_id')


            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id or user_id is missing.",
                })

           
            
            

            try:
            
                if task_id:
                    task_ids = [int(tid) for tid in task_id.split(',')]
                    tasks = Tasks.objects.filter(
                    id__in=task_ids, created_by=user_id, inTrash=True
                    ).update(inTrash=False)
                    
                    
                    # Filter TaskChecklist objects and update inTrash and trashed_with fields
                    updated_task_checklist_queryset = TaskChecklist.objects.filter(
                        Task__in=task_ids,
                        created_by=user_id, 
                        inTrash=True,
                        trashed_with="Relatively_task"
                    )
            
                    # Update inTrash and trashed_with fields and get the IDs of updated objects
                    updated_task_checklist_ids = updated_task_checklist_queryset.values_list('id', flat=True)
                   

                    filtered_checklist_task = SubTasks.objects.filter(task_checklist__in=updated_task_checklist_ids, 
                                                                            created_by=user_id, inTrash=True,trashed_with="Relatively_task" ).update(inTrash=False, trashed_with=None)
                    updated_task_checklist_queryset.update(inTrash=False, trashed_with=None)
                    
                if task_checklist:
                    task_checklist_ids = [int(tid) for tid in task_checklist.split(',')]
                    TaskChecklist.objects.filter(id__in=task_checklist_ids,
                                                                        created_by=user_id, inTrash=True,trashed_with="Manually" ).update(inTrash=False, trashed_with=None)
                    SubTasks.objects.filter(task_checklist__in=task_checklist_ids, 
                                                                        created_by=user_id, inTrash=True,trashed_with="Relatively_checklist" ).update(inTrash=False, trashed_with=None)
                if checklist_tasks:
                    checklist_tasks_ids = [int(tid) for tid in checklist_tasks.split(',')]
                    filtered_checklist_task = SubTasks.objects.filter(id__in=checklist_tasks_ids, 
                                                                            created_by=user_id, inTrash=True,trashed_with="Manually" ).update(inTrash=False, trashed_with=None)
                
                
                if not task_id and not task_checklist and not checklist_tasks:
                    tasks = Tasks.objects.filter(
                    created_by=user_id, inTrash=True
                    ).update(inTrash=False)
                    filtered_task_checklist = TaskChecklist.objects.filter(created_by=user_id, 
                                                                           inTrash=True).update(inTrash=False, trashed_with=None)
                    
                    filtered_checklist_task = SubTasks.objects.filter(created_by=user_id,
                                                                            inTrash=True).update(inTrash=False, trashed_with=None)

                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Restored successfully",
                })
            except Exception as e:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": str(e),
                })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to restored Trash",
                "errors": str(e),
            })
            

    @csrf_exempt
    def PermanantdeleteTask(self, request):
        task_id = request.GET.get('task_id')
        task_checklist = request.GET.get('task_checklist')
        checklist_tasks = request.GET.get('checklist_tasks')
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
                tasks = Tasks.objects.filter(
                id__in=task_ids, created_by=user_id, inTrash=True
                )
                tasks.delete()
                
            if task_checklist:
                task_checklist_ids = [int(tid) for tid in task_checklist.split(',')]
                filtered_task_checklist = TaskChecklist.objects.filter(id__in=task_checklist_ids, created_by=user_id, inTrash=True,trashed_with="Manually" )
                filtered_task_checklist.delete()
            if checklist_tasks:
                checklist_tasks_ids = [int(tid) for tid in checklist_tasks.split(',')]
                filtered_checklist_task = SubTasks.objects.filter(id__in=checklist_tasks_ids, created_by=user_id, inTrash=True,trashed_with="Manually" )
                filtered_checklist_task.delete()
            
            if not task_id and not task_checklist and not checklist_tasks:
                tasks = Tasks.objects.filter(
                created_by=user_id, inTrash=True
                )
                filtered_task_checklist = TaskChecklist.objects.filter(created_by=user_id, inTrash=True,trashed_with="Manually" )
                
                filtered_checklist_task = SubTasks.objects.filter(created_by=user_id, inTrash=True,trashed_with="Manually" )
                tasks.delete()
                filtered_task_checklist.delete()
                filtered_checklist_task.delete()
                    

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

        
  