from django.http import JsonResponse
from digielves_setup.helpers.error_trace import create_error_response
from digielves_setup.models import  EmployeePersonalDetails, TaskHierarchy, TaskHierarchyChecklist,  TaskStatus, User
from employee.seriallizers.task_hierarchy.task_hierarchy_checklist_seriallizers import AddTaskHierarchyChecklistsSerializer, GetTaskHierarchyChecklistsSerializer
from employee.seriallizers.task_seriallizers import GetChecklistTasksSerializer, GetTaskChecklistSerializer, GetTaskChecklistsSerializer, TaskChecklistSerializer
from rest_framework import status
from rest_framework.decorators import api_view

from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from django.core.serializers import serialize
from django.db.models import Q
from django.db.models import Count


class TaskHierarchyChecklistViewSet(viewsets.ModelViewSet):
    serializer_class = GetTaskHierarchyChecklistsSerializer


    @csrf_exempt
    def create_task_checklist(self,request):
        
        serializer = AddTaskHierarchyChecklistsSerializer(data=request.data)

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
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
            
      
            
    
    @csrf_exempt
    def get_task_hierarchy_checklists(self, request):
        
        task_id = request.GET.get('task_id')
        user_id = request.GET.get('user_id')

        if not task_id or not user_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. Both task_id and user_id are required."
            })

        try:
            task = TaskHierarchy.objects.get(id=task_id)
            
            task_checklist = TaskHierarchyChecklist.objects.filter(Task= task, inTrash = False)

            checklist_serializer = GetTaskHierarchyChecklistsSerializer(task_checklist, many=True)


            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task Checklist retrieved successfully.",
                "data": checklist_serializer.data
            })
        except TaskHierarchy.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Task not found.",
            })
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    


    
    @csrf_exempt
    def update_checklist_fields(self, request):
        try:
            check_id = request.data.get('checklist_id')
            user_id = request.data.get('user_id')

            if not (check_id and user_id):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id and check_id are required."
                })

            check = TaskHierarchyChecklist.objects.get(id=check_id)
 
            
            
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
           
            
            check.save()



            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Checklist updated successfully."
            }

            return JsonResponse(response)

        except TaskHierarchyChecklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Checklist not found.",
            })
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @csrf_exempt
    def delete_checklistData(self, request):
        check_id = request.GET.get('checklist_id')
        user_id = request.GET.get('user_id')
        
        
        try:
            
            check = TaskHierarchyChecklist.objects.get(id=check_id, created_by=user_id)
        except TaskHierarchyChecklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": "You don't have permission to delete this checklist",
            })

        try:
            check = TaskHierarchyChecklist.objects.get(id=check_id)
        except TaskHierarchyChecklist.DoesNotExist:
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
    
 
    
    