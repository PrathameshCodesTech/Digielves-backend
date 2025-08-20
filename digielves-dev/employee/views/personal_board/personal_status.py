
from digielves_setup.models import PersonalStatus, PersonalTask, User
from employee.seriallizers.personal_board.personal_board_seriallizers import PersonalStatusSerializer
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Prefetch 
from django.db import transaction
from django.db.models import Max
from django.db.models import Q


class PersonalStatusViewSet(viewsets.ModelViewSet):

    # serializer_class = organizationBranchSerializer
 
    @csrf_exempt
    def AddPersonalStatus(self, request):
        user_id = request.data.get('user_id')
        status_name = request.data.get('status_name')
        fixed_state = request.data.get('fixed_state')
        color = request.data.get('color')
        order = request.data.get('order')

        try:
            with transaction.atomic():
                if not user_id:
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid request. Please provide either admin_id or org_id.",
                        "data": {}
                    })
                
                
                if PersonalStatus.objects.filter(user_id=user_id, status_name=status_name).exists():
                    return JsonResponse({
                        "success": False,
                        "status": 123,  # Error code for existing status
                        "message": f"Status with name '{status_name}' already exists."
                    })
                
                user_id = User.objects.get(id = user_id)
                # Add the user-specified status
                PersonalStatus.objects.create(
                    user_id=user_id,
                    status_name=status_name,
                    fixed_state=fixed_state,
                    color=color,
                    order=order
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
    def updatePersonalTasksStatusField(self, request):
        try:
            status_id = request.data.get('status_id')
            user_id = request.data.get('user_id')

            if not (status_id and user_id):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. status_id and user_id are required."
                })

            task_status = PersonalStatus.objects.get(id=status_id,user_id =user_id)

            
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

        except PersonalStatus.DoesNotExist:
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

            if not user_id :
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id are required."
                })


            Personal_task_statuses = PersonalStatus.objects.filter(user_id=user_id).order_by('order')

            serializer = PersonalStatusSerializer(Personal_task_statuses, many=True)

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

        except User.DoesNotExist:
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
            status_id = request.GET.get('status_id')
            confirm = int(request.GET.get('confirm', 0))  # Convert confirm to integer
            to_status = request.GET.get('to_status', None)
            
            # Check for required parameters
            if not user_id :
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "user_id  are required for Admin."
                })

            
            # Define response dictionary
            response_data = {
                "success": True,
                "status": status.HTTP_200_OK,
            }

            # Handle different confirmation cases
            if confirm == 0 or confirm == -1:
                # Get task count
                task_count = PersonalTask.objects.filter(status=status_id, inTrash=False).count()
                response_data["data"] = {"task_count": task_count}
                if confirm == 0 and task_count == 0:
                    # Delete status if confirm is 0 and task count is 0
                    PersonalStatus.objects.get(id=status_id).delete()
                return JsonResponse(response_data)

            elif confirm == 2:
                # Move tasks to other status
                to_task_status = PersonalStatus.objects.get(id=to_status)
                PersonalTask.objects.filter(status=status_id, inTrash=False).update(status=to_task_status.id)
                PersonalStatus.objects.get(id=status_id).delete()
                
                response_data["message"] = "Tasks moved to another status successfully."
            
            else:
                # Default case: delete status
                PersonalStatus.objects.get(id=status_id).delete()
                response_data["message"] = "TaskStatus object deleted successfully."

            return JsonResponse(response_data)

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
                "message": f"An error occurred: {str(e)}",
            })
