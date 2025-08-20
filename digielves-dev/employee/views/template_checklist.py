from django.http import JsonResponse
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from digielves_setup.models import Checklist, TemplateChecklist

from employee.seriallizers.template_seriallizers import TemplateCheckListSerializer

class TemplateChecklistViewSet(viewsets.ModelViewSet):
    serializer_class = TemplateCheckListSerializer

    @csrf_exempt
    def create(self, request):
        print(request.data)
        serializer = TemplateCheckListSerializer(data=request.data)
        try:
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Template checklist created successfully.",
                    "data": serializer.data
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create template checklist.",
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
    def getChecklistData(self, request):
        try:
            template_id = request.GET.get('template_id')
            checklists = TemplateChecklist.objects.filter(template_id=template_id)
            serializer = TemplateCheckListSerializer(checklists, many=True)
            data = serializer.data

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Checklist data retrieved successfully",
                "data": data
            })
        except TemplateChecklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Template checklist not found."
            })
    @csrf_exempt
    def updateChecklistData(self, request):
        checklist_id = request.data.get('checklist_id')
        try:
            checklist = TemplateChecklist.objects.get(id=checklist_id)
        except TemplateChecklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Checklist not found",
            })

        serializer = TemplateCheckListSerializer(checklist, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Checklist updated successfully",
                "data": serializer.data
            })
        return JsonResponse({
            "success": False,
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid data",
            "errors": serializer.errors
        })
    @csrf_exempt
    def deleteChecklistData(self, request):
        checklist_id = request.data.get('checklist_id')
        try:
            checklist = TemplateChecklist.objects.get(id=checklist_id)
        except TemplateChecklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Checklist not found",
            })

        checklist.delete()
        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "Checklist deleted successfully",
        })
    
    






