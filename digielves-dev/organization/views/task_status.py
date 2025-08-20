

from digielves_setup.models import TaskHierarchy, SubTasks, DoctorPersonalDetails, OrganizationBranch, OrganizationDetails, EmployeePersonalDetails, TaskChecklist, TaskStatus, Tasks, User
from organization.seriallizers.organization_branch_seriallizer import EmployeeSerializer, GetOrganizationDetailsSerializer, OrganizationBranchSerializer, OrganizationDetailsSerializer, organizationBranchSerializer
from organization.seriallizers.organization_details_seriallizer import organizationDetailsSerializer
from organization.seriallizers.task_status_seriallizers import TaskStatusSerializer, TasksSerializerOrganization
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Prefetch 
from django.db import transaction
from django.db.models import Max
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
from django.db.models import F, Func, Value

class Replace(Func):
    function = 'REPLACE'
    
    
    
class CustomPagination(PageNumberPagination):
    page_size = 10  # Number of tasks per page
    page_size_query_param = 'page_size'
    max_page_size = 1000
    
    
class TasksStatusViewSet(viewsets.ModelViewSet):

    serializer_class = organizationBranchSerializer
 
    @csrf_exempt
    def AddStatus(self, request):
        user_id = request.data.get('user_id')
        admin_id = request.data.get('admin_id')
        org_id = request.data.get('org_id')
        status_name = request.data.get('status_name')
        fixed_state = request.data.get('fixed_state')
        color = request.data.get('color')
        order = request.data.get('order')

        try:
            with transaction.atomic():
                if admin_id and org_id:
                  
                    admin_user = User.objects.get(id=admin_id, user_role="Dev::Admin")
                    organization_id = User.objects.get(id=org_id, user_role="Dev::Organization")
                    
                elif org_id:
                    organization_id = User.objects.get(id=org_id, user_role="Dev::Organization")
                else:
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid request. Please provide either admin_id or org_id.",
                        "data": {}
                    })

                
                org_details = OrganizationDetails.objects.get(user_id=organization_id)
                
                
                if TaskStatus.objects.filter(organization=org_details, status_name=status_name).exists():
                    return JsonResponse({
                        "success": False,
                        "status": 123,  # Error code for existing status
                        "message": f"Status with name '{status_name}' already exists."
                    })
                # Check if 'Closed' status is available
                close_status = TaskStatus.objects.filter(organization=org_details, fixed_state='Closed')
                

                # Add the user-specified status
                user_status = TaskStatus.objects.create(
                    user_admin=admin_user if admin_id else None,
                    organization=org_details,
                    status_name=status_name,
                    fixed_state=fixed_state,
                    color=color,
                    order=order
                )
                
                if not close_status:
                    # If 'Done' status is not available, add it first
                    max_order = TaskStatus.objects.filter(organization=org_details).aggregate(Max('order'))['order__max']
                    close_status = TaskStatus.objects.create(
                        user_admin=admin_user if admin_id else None,
                        organization=org_details,
                        status_name='Closed',
                        fixed_state='Closed',
                        color='#33cc33',
                        order=max_order + 1 if max_order else 1
                    )

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Status added successfully."
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
                "message": f"An error occurred: {str(e)}"
            })

    @csrf_exempt
    def updateTasksStatusField(self, request):
        try:
            status_id = request.data.get('status_id')
            user_id = request.data.get('user_id')

            if not (status_id and user_id):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. status_id and user_id are required."
                })
                
            
                
            is_user = User.objects.get(Q(user_role="Dev::Organization") | Q(user_role="Dev::Admin"), id=user_id)
            
            if is_user:
                
                if is_user.user_role == "Dev::Organization":
                    
                    org_details = OrganizationDetails.objects.get(user_id=is_user)
                   
                    try:
                        check_user_auth = TaskStatus.objects.get(id=status_id,organization=org_details)
                    
                    except Exception as e:
                        return JsonResponse({
                                "success": False,
                                "status": status.HTTP_404_NOT_FOUND,
                                "message": "You are not allowed to update status fields.",
                            })
                    


            task_status = TaskStatus.objects.get(id=status_id)

            
            fixed_state = request.data.get('fixed_state')
            if fixed_state is not None:
                task_status.fixed_state = fixed_state
                        
            color = request.data.get('color')
            if color is not None:
                task_status.color = color
            
            order = request.data.get('order')
            if order is not None:
                task_status.order = order
            
            status_name = request.data.get('status_name')
            if status_name is not None:
                task_status.status_name = status_name

            task_status.save()


            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task updated successfully."
            }

            return JsonResponse(response)

        except TaskStatus.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Task Status not found.",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update Task Status.",
                "errors": str(e)
            })
    
    @csrf_exempt
    def getStatuses(self, request):
        try:
            user_id = request.GET.get('user_id')
            org_id = request.GET.get('org_id')

            if not user_id or (not org_id and User.objects.get(id=user_id).user_role == "Dev::Admin"):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. Both user_id and org_id are required for Admin."
                })

            is_user = User.objects.get(Q(user_role="Dev::Organization") | Q(user_role="Dev::Admin"), id=user_id)

            if is_user.user_role == "Dev::Admin":
                org_details = OrganizationDetails.objects.get(user_id=org_id)
            else:
                org_details = OrganizationDetails.objects.get(user_id=user_id)

            task_statuses = TaskStatus.objects.filter(organization=org_details).order_by('order')

            serializer = TaskStatusSerializer(task_statuses, many=True)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "TaskStatus objects retrieved successfully.",
                "data": serializer.data
            })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found."
            })

        except OrganizationDetails.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Organization details not found."
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"An error occurred: {str(e)}",
            })
    # if 0 send task count , if 1 delete (in our case we are just making a null in task side) if two move to other status
    @csrf_exempt
    def deleteStatus(self, request):
        try:
            user_id = request.GET.get('user_id')
            org_id = request.GET.get('org_id')
            status_id = request.GET.get('status_id')
            confirm = int(request.GET.get('confirm', 0))  # Convert confirm to integer
            to_status = request.GET.get('to_status', None)
            
            # Check for required parameters
            if not user_id or (not org_id and User.objects.get(id=user_id).user_role == "Dev::Admin"):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Both user_id and org_id are required for Admin."
                })

            # Get organization details
            if User.objects.get(id=user_id).user_role == "Dev::Admin":
                org_details = OrganizationDetails.objects.get(user_id=org_id)
            else:
                org_details = OrganizationDetails.objects.get(user_id=user_id)
            
            # Define response dictionary
            response_data = {
                "success": True,
                "status": status.HTTP_200_OK,
            }

            # Handle different confirmation cases
            if confirm == 0 or confirm == -1:
                # Get task count
                task_count = Tasks.objects.filter(status=status_id, inTrash=False).count()
                checklist_task_count = SubTasks.objects.filter(status=status_id).count()
                response_data["data"] = {"task_count": task_count+checklist_task_count}
                if confirm == 0 and task_count == 0:
                    # Delete status if confirm is 0 and task count is 0
                    TaskStatus.objects.get(id=status_id).delete()
                return JsonResponse(response_data)

            elif confirm == 2:
                # Move tasks to other status
                to_task_status = TaskStatus.objects.get(id=to_status)
                Tasks.objects.filter(status=status_id, inTrash=False).update(status=to_task_status.id)
                SubTasks.objects.filter(status=status_id).update(status=to_task_status.id)
                TaskChecklist.objects.filter(status=status_id).update(status=to_task_status.id)
                TaskStatus.objects.get(id=status_id).delete()
                
                response_data["message"] = "Tasks moved to another status successfully."
            
            else:
                # Default case: delete status
                TaskStatus.objects.get(id=status_id).delete()
                response_data["message"] = "TaskStatus object deleted successfully."

            return JsonResponse(response_data)

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found."
            })

        except OrganizationDetails.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Organization details not found."
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"An error occurred: {str(e)}",
            })

    @csrf_exempt
    def get_org_task(self, request):
        user_id = request.GET.get('user_id')
        page = request.GET.get('page', 1)
    
        try:
            user_check = User.objects.filter(id=user_id, user_role='Dev::Organization').first()
            if not user_check:
                return JsonResponse({"success": False, "message": "You don't have permission"})
    
            # Get the organization
            org_detail = OrganizationDetails.objects.filter(user_id=user_check).first()
            if not org_detail:
                return JsonResponse({"success": False, "message": "Organization not found"})
    
            # Get all users under this organization
            org_user_ids = EmployeePersonalDetails.objects.filter(organization_id=org_detail).values_list('user_id', flat=True)
    
        except Exception as e:
            return JsonResponse({"success": False, "message": "You don't have permission", "error": str(e)})
    
        cache_key = f'task_list1_{user_id}_page_{page}'
        cached_response = cache.get(cache_key)
    
        if cached_response:
            return JsonResponse({
                "success": True,
                "status": 200,
                "message": "Task List",
                "data": cached_response['data']
            })
    
        try:
            all_task = TaskHierarchy.objects.filter(
                created_by__in=org_user_ids,
                is_personal=False,
                inTrash=False,
                status__isnull=False
            )
    
            paginator = CustomPagination()
            paginated_tasks = paginator.paginate_queryset(all_task, request)
    
            serialized_data = TasksSerializerOrganization(paginated_tasks, many=True).data
    
            response_data = {
                "success": True,
                "status": 200,
                "message": "Task List",
                "data": serialized_data,
            }
    
            cache.set(cache_key, response_data, timeout=120)
            return JsonResponse(response_data)
    
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to get Task.",
                "errors": str(e)
            })
