import random
from django.http import JsonResponse
import pytz
from configuration.gzipCompression import compress

from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.core.files.storage import FileSystemStorage

# import datetime
from django.contrib.contenttypes.models import ContentType
from django.core.serializers import serialize
from django.shortcuts import get_object_or_404
from digielves_setup.models import   PersonalStatus, PersonalTask, PersonalTaskAttachments,  User, UserFilters
from configuration import settings


from employee.seriallizers.personal_board.personal_board_seriallizers import  GetPersonalStatusSerializer, PersonalTaskAttachmentSerializer, PersonalTaskSerializer

class PersonalTaskViewSet(viewsets.ModelViewSet):
    serializer_class = PersonalTaskSerializer

    


            
    @csrf_exempt
    def personal_create_task(self, request):
     
        serializer = PersonalTaskSerializer(data=request.data)

        try:
            
            if serializer.is_valid():
                

                task = serializer.save()

           
                attachments = request.FILES.getlist('attachments')

                for attachment in attachments:
                    try:
                        task_attachment = PersonalTaskAttachments.objects.create(personaltask_id=task, attachment=attachment)
                       
                    except Exception as e:
                        return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Failed to create Task.",
                            "errors": f"Failed to process attachment: {attachment.name}. Error: {str(e)}"
                        })




                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Task created successfully."
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
    def personal_get_task(self,request):
        try:
            user_id = request.GET.get('user_id')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id is missing."
                })

            personalTask = PersonalTask.objects.filter(user_id=user_id, inTrash=False).order_by('due_date')
            task_statuses = PersonalStatus.objects.filter(user_id=user_id).order_by('order', 'created_at')
            fixed_state_titles_and_ids = [(status.status_name, status.fixed_state, status.order, status.id) for status in task_statuses]

            data = [
                {"id": f"s_{status_id}", "title": title, "fixed_state": fix_state, "order": order, "status_id": status_id, "tasks": []}
                for title, fix_state, order, status_id in fixed_state_titles_and_ids
            ]

            if personalTask.exists():
                for task in personalTask:
                    IST = pytz.timezone('Asia/Kolkata')
                
                    due_date_ist = task.due_date.astimezone(IST) if task.due_date else None
                    task_data = {
                        "id": f"t_{task.id}",
                        "title": task.task_topic,
                        "description": task.task_description,
                        "due_date": due_date_ist,
                        "urgent_status": task.urgent_status,
                        "status": task.status.id if task.status else None,
                        "reopened_count": task.reopened_count,
                        "created_at": task.created_at.isoformat()
                    }

                    for idx, (title, fix_state, order, status_id) in enumerate(fixed_state_titles_and_ids):
                        if task.status and task.status.id == status_id:
                            status_info = {
                                "id": task.status.id,
                                "status_name": task.status.status_name,
                                "color": task.status.color,
                            }
                            task_data["status"] = status_info
                            data[idx]["tasks"].append(task_data)
                            break

            try:
                board_view = UserFilters.objects.get(user=user_id).personal_board_view
            except UserFilters.DoesNotExist:
                board_view = None

            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "User tasks retrieved successfully.",
                "data": data,
                "board_view": board_view
            }

            return JsonResponse(response)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve user tasks.",
                "errors": str(e)
            })
    
    @csrf_exempt
    def get_personal_task_attachment_data(self,request):
        try:
            task_id = request.GET.get('task_id')
            user_id = request.GET.get('user_id')

            if not task_id and not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id and user_id is missing."
                })

            task_attachments = PersonalTaskAttachments.objects.filter(personaltask_id=task_id)
            if not task_attachments.exists():
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "No attachments found for the given task_id."
                })

            serializer = PersonalTaskAttachmentSerializer(task_attachments, many=True)
            data = serializer.data

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task attachment data retrieved successfully.",
                "data": data
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error.",
                "errors": str(e)
            })
            
            
    @csrf_exempt
    def create_personal_TaskAttachment(self, request):
        try:
            task_id = request.POST.get('task_id')
            attachments = request.FILES.getlist('attachments')
            user_id = request.POST.get('user_id')

            if not task_id or not attachments or not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id or attachments  or user_id are missing."
                })

            task = PersonalTask.objects.filter(id=task_id).first()
            if not task:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task not found."
                })

            try:
                
                
                
                attachments = request.FILES.getlist('attachments')

                for attachment in attachments:
                    try:
                        PersonalTaskAttachments.objects.create(personaltask_id=task, attachment=attachment)
                       
                    except Exception as e:
                        return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Failed to create Task.",
                            "errors": f"Failed to process attachment: {attachment.name}. Error: {str(e)}"
                        })
                        
                        
              

                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Task attachments created successfully."
                    })
            except Exception as e:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to Add Attachments.",
                    "errors": str(e)
                })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to create Task attachments.",
                "errors": str(e)
            })
            
        
    
    @csrf_exempt
    def personal_task_update(self, request):
        try:
            task_id = request.data.get('task_id')
            user_id = request.data.get('user_id')

            if not (task_id and user_id):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id and user_id are required."
                })

            task = PersonalTask.objects.get(id=task_id,user_id = user_id)

            
            due_date = request.data.get('due_date')
            if due_date is not None:
                task.due_date = due_date

            
            desc = request.data.get('task_description')
            if desc is not None:
                task.task_description = desc
            
            topic = request.data.get('task_topic')
            if topic is not None:
                task.task_topic = topic
            
            Status = request.data.get('status')
            if Status is not None:
                personal_status = PersonalStatus.objects.get(id=Status)
                task.status = personal_status
                
            task.save()
            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task updated successfully."
            }

            return JsonResponse(response)

        except PersonalTask.DoesNotExist:
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
    def personal_task_delete(self, request):
        task_id = request.GET.get('task_id')
        user_id = request.GET.get('user_id')
        print(task_id)
        try:
            task = PersonalTask.objects.get(id=task_id,user_id = user_id)
        except PersonalTask.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Tasks not found",
            })
        task.delete()
        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "Tasks deleted successfully",
        })  
        
    
    @csrf_exempt
    def get_personal_statuses(self, request):
        try:
            user_id = request.GET.get('user_id')

            if not user_id :
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id are required."
                })


            Personal_task_statuses = PersonalStatus.objects.filter(user_id=user_id).order_by('order')

            serializer = GetPersonalStatusSerializer(Personal_task_statuses, many=True)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "status retrieved successfully.",
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
                "message": f"An error occurred: {str(e)}",
            })
            
    
    @csrf_exempt
    def delete_personal_task_attachment(self, request):
        try:
            attachment_id = request.GET.get('attachment_id')
            user_id = request.GET.get('user_id')
            

            if not attachment_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. attachment_id is missing.",
                    
                })

            task_attachment = PersonalTaskAttachments.objects.get(id=attachment_id).delete()
            if not task_attachment:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task attachment not found."
                })

            

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task attachment deleted successfully."
                })


        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to delete Task attachment.",
                "errors": str(e)
            })

    