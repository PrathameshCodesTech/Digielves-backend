import random
from django.http import JsonResponse
from employee.seriallizers.task_hierarchy.task_hierarchy_seriallizers import TaskHierarchyAttachmentSerializer
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from configuration import settings
from digielves_setup.models import TaskAttachments, TaskHierarchy, TaskHierarchyAttachments, Tasks, TemplateChecklist, User
from employee.seriallizers.attachment_seriallizers import AttachmentSerializer
from django.core.files.base import ContentFile
from employee.seriallizers.template_seriallizers import TemplateCheckListSerializer
import os
class TaskHierarchyAttachmentViewSet(viewsets.ModelViewSet):
    
    @csrf_exempt
    def create_task_attachment(self, request):
        try:
            task_id = request.POST.get('task_id')
            user_id = request.POST.get('user_id')
            attachments = request.FILES.getlist('attachment')

            if not task_id or not attachments:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id or attachments are missing."
                })

            task = TaskHierarchy.objects.filter(id=task_id).first()
            if not task:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task not found."
                })

            try:
           

                attachment_data = []
                user = User.objects.get(id = user_id)

                for attachment in attachments:
                    

                    task_attachment = TaskHierarchyAttachments(created_by=user ,task=task, task_attachment=attachment)
                    task_attachment.save()

                    attachment_data.append({
                        "id": task_attachment.id,
                    })

                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Task attachments created successfully.",
                    "attachments": attachment_data
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
    def get_task_attachments(self, request):
        try:
            task_id = request.GET.get('task_id')
            user_id = request.GET.get('user_id')
            if task_id:
                task_attachment = TaskHierarchyAttachments.objects.filter(task_id=task_id)
                serializer = TaskHierarchyAttachmentSerializer(task_attachment, many=True)
                data = serializer.data

                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Task Attachment data retrieved successfully",
                    "data": data
                })
            
        except TemplateChecklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Task Attachment not found."
            })
    



                

    @csrf_exempt
    def delete_task_attachment(self, request):
        try:
            attachment_id = request.GET.get('attachment_id')
            task_id = request.GET.get('task_id')
            user_id = request.GET.get('user_id')
            

            if not attachment_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. attachment_id is missing.",
                    
                })

            task_attachment = TaskHierarchyAttachments.objects.filter(id=attachment_id).first()
            if not task_attachment:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task attachment not found."
                })

            file_path = task_attachment.task_attachment.path 
            try:
                
            
                task_attachment.delete()
                if os.path.exists(file_path):
                    os.remove(file_path)


                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Task attachment deleted successfully."
                    })

            except Exception as e:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to delete Task attachment.",
                    "errors": str(e)
                })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to delete Task attachment.",
                "errors": str(e)
            })


