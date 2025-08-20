import random
from django.http import JsonResponse
from employee.seriallizers.sales_attachment_seriallizers import SalesAttachmentSerializer
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from configuration import settings
from digielves_setup.models import SalesAttachments, SalesLead, TaskAttachments, Tasks, TemplateChecklist
from employee.seriallizers.attachment_seriallizers import AttachmentSerializer
from django.core.files.base import ContentFile
from employee.seriallizers.template_seriallizers import TemplateCheckListSerializer
import os
class SalesAttachmentViewSet(viewsets.ModelViewSet):
    
    @csrf_exempt
    def createSalesAttachment(self, request):
        try:
            sales_lead_id = request.data.get('sales_lead_id')
            attachment = request.data.get('attachment')
            user_id = request.data.get('user_id')
            if not sales_lead_id or not attachment or not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id or attachments are missing."
                })

            sales_lead = SalesLead.objects.get(id=sales_lead_id)
            SalesAttachments.objects.create(sales_lead=sales_lead, attachment=attachment)
            
            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Sales lead attachments created successfully."
                })
           

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to create Sales attachments.",
                "errors": str(e)
            })


    @csrf_exempt
    def getSalesAttachment(self, request):
        try:
            user_id = request.GET.get('user_id')
            sales_lead_id = request.GET.get('sales_lead_id')
            if sales_lead_id:
                sales_attachment = SalesAttachments.objects.filter(sales_lead=sales_lead_id)
                serializer = SalesAttachmentSerializer(sales_attachment, many=True)
                data = serializer.data

                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Sales Attachment data retrieved successfully",
                    "data": data
                })
            else:
                pass
        except TemplateChecklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Sales Attachment not found."
            })
    



    
            

    @csrf_exempt
    def deleteSalesAttachment(self, request):
        try:
            user_id = request.GET.get('user_id')
            sales_lead_id = request.GET.get('sales_lead_id')
            attachment_id = request.GET.get('attachment_id')
            

            if not attachment_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. attachment_id is missing.",
                    
                })

            SalesAttachments.objects.get(id=attachment_id).delete()
            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Sales attachment Deleted successfully.",
                  
                })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to delete Task attachment.",
                "errors": str(e)
            })


