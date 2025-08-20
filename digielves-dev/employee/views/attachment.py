import random
from django.http import JsonResponse
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from configuration import settings
from digielves_setup.models import TaskAttachments, Tasks, TemplateChecklist
from employee.seriallizers.attachment_seriallizers import AttachmentSerializer
from django.core.files.base import ContentFile
from employee.seriallizers.template_seriallizers import TemplateCheckListSerializer
import os
class AttachmentViewSet(viewsets.ModelViewSet):
    
    @csrf_exempt
    def createTaskAttachment(self, request):
        try:
            task_id = request.POST.get('task_id')
            print(task_id)
            attachments = request.FILES.getlist('attachment')
            print(attachments)

            if not task_id or not attachments:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id or attachments are missing."
                })

            task = Tasks.objects.filter(id=task_id).first()
            if not task:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task not found."
                })

            try:
                print("---------------------------------------ahay----------")
                user_folder = settings.MEDIA_ROOT
                print(user_folder)

                attachment_data = []
                print("---------------------------------------ahay")

                for attachment in attachments:
                    print("---------------------------------------ahay1")
                    filename = os.path.join('employee', 'task_attachment', attachment.name)
                    file_path = os.path.join(user_folder, filename)
                    print("---------------------------------------ahay2")
                    
                    #filename = '/employee/task_attachment/' + attachment.name
                    try:
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        with open(file_path, 'wb') as f:
                            f.write(attachment.read())

    
                        task_attachment = TaskAttachments(task=task, attachment=filename)
                        task_attachment.save()
    
                        attachment_data.append({
                            "id": task_attachment.id,
                            "attachment": filename,
                        })
                    except Exception as e:
                        return JsonResponse({
                            "success": False,
                            "status": 400,
                            "message": "Failed to Add Attachments.",
                            "errors": str(e)
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

    # @csrf_exempt
    # def createTaskAttachment(self, request):
    #     try:
    #         task_id = request.POST.get('task_id')
    #         print(task_id)
    #         attachment = request.FILES.get('attachment')

    #         if not task_id or not attachment:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": status.HTTP_400_BAD_REQUEST,
    #                 "message": "Invalid request. task_id or attachment is missing."
    #             })

    #         task = Tasks.objects.filter(id=task_id).first()
    #         if not task:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": status.HTTP_404_NOT_FOUND,
    #                 "message": "Task not found."
    #             })


    #         try:
    #             user_folder = settings.MEDIA_ROOT 
    #             print(user_folder)
                

    #             filename =  '/employee/task_attachment/' + attachment.name
                
    #             with open(user_folder + filename, 'wb') as f:
    #                 f.write(attachment.read())
    #             task_attachment = TaskAttachments(task=task, attachment=filename)
    #             task_attachment.save()


    #             attachments = TaskAttachments.objects.filter(task__id=task_id)
    #             attachment_serializer = AttachmentSerializer(attachments, many=True)

                
                
    #             attachment_data = attachment_serializer.data

    #             return JsonResponse({
    #             "success": True,
    #             "status": status.HTTP_201_CREATED,
    #             "message": "Task attachment created successfully.",
    #             "attachments": attachment_data
    #         })
    #         except Exception as e:
    #             return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_400_BAD_REQUEST,
    #             "message": "Failed to Add Attachment.",
    #             "errors": str(e)
    #         })


    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "Failed to create Task attachment.",
    #             "errors": str(e)
    #         })

    @csrf_exempt
    def getTaskAttachmentData(self, request):
        try:
            task_id = request.GET.get('task_id')
            if task_id:
                task_attachment = TaskAttachments.objects.filter(task_id=task_id)
                serializer = AttachmentSerializer(task_attachment, many=True)
                data = serializer.data

                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Task Attachment data retrieved successfully",
                    "data": data
                })
            else:
                    task = TaskAttachments.objects.all()
                    serializer = AttachmentSerializer(task, many=True)
                    return JsonResponse({
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "message": "Task Attachment retrieved successfully",
                        "data": serializer.data
                    })
        except TemplateChecklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Task Attachment not found."
            })
    



    @csrf_exempt
    def updateTaskAttachment(self, request):
        try:
            attachment_id = request.data.get('attachment_id')
            attachment = request.FILES.get('attachment')

            if not attachment_id or not attachment:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. attachment_id or attachment is missing."
                })

            task_attachment = TaskAttachments.objects.filter(id=attachment_id).first()
            if not task_attachment:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task attachment not found."
                })

            
            previous_attachment_path = os.path.join(settings.MEDIA_ROOT, task_attachment.attachment)

            try:
                
                if os.path.exists(previous_attachment_path):
                    os.remove(previous_attachment_path)

                user_folder = settings.MEDIA_ROOT
                filename = '/employee/task_attachment/attachment_' + ''.join(random.choices('0123456789', k=12)) + "_" + str(task_attachment.task.id) + '.jpeg'
                with open(user_folder + filename, 'wb') as f:
                    f.write(attachment.read())

                task_attachment.attachment = filename
                task_attachment.save()

                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Task attachment updated successfully.",
                    "data": {
                        "id": task_attachment.id,
                        "task": task_attachment.task.id,
                        "attachment": task_attachment.attachment,
                        "created_at": task_attachment.created_at
                    }
                })

            except Exception as e:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to update Task attachment.",
                    "errors": str(e)
                })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update Task attachment.",
                "errors": str(e)
            })\
            

    @csrf_exempt
    def deleteTaskAttachment(self, request):
        try:
            attachment_id = request.GET.get('attachment_id')
            task_id = request.GET.get('task_id')
            

            if not attachment_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. attachment_id is missing.",
                    
                })

            task_attachment = TaskAttachments.objects.filter(id=attachment_id).first()
            if not task_attachment:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task attachment not found."
                })

            
            attachment_path = os.path.join(settings.MEDIA_ROOT, task_attachment.attachment)

            try:
                
                if os.path.exists(attachment_path):
                    os.remove(attachment_path)

                task_attachment.delete()
                if task_id:
                    task_attachment = TaskAttachments.objects.filter(task_id=task_id)
                    serializer = AttachmentSerializer(task_attachment, many=True)
                    data = serializer.data

                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Task attachment deleted successfully.",
                    "attachments": data
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


