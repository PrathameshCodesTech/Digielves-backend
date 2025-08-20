from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import JsonResponse

from rest_framework import status
from digielves_setup.models import TemplateChecklist, TemplateTaskList

from employee.seriallizers.template_seriallizers import TemplateCheckListSerializer, TemplateCheckListTaskSerializer
from django.views.decorators.csrf import csrf_exempt

class TemplateTaskListViewSet(viewsets.ModelViewSet):
    serializer_class = TemplateCheckListTaskSerializer

    @csrf_exempt
    def CreateTask(self, request):
        
        print("------------pahlelele-----------")
        serializer = TemplateCheckListTaskSerializer(data=request.data)
        try:
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Template task list created successfully.",
                    "data": serializer.data
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create template task list.",
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
    def getCheckListTaskData(self, request):
        try:
            checklist_id = request.GET.get('checklist_id')
            task_list = TemplateTaskList.objects.filter(checklist_id=checklist_id)
            serializer = TemplateCheckListTaskSerializer(task_list, many=True)
            data = serializer.data

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task data retrieved successfully",
                "data": data
            })
        except TemplateChecklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Template checklist not found."
            })

        
    @csrf_exempt
    def updateTask(self, request):
        task_id = request.data.get('task_id')
        print(task_id)
        try:
            task = TemplateTaskList.objects.get(id=task_id)
        except TemplateTaskList.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "task id not found",
            })

        serializer = TemplateCheckListTaskSerializer(task, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task updated successfully",
                "data": serializer.data
            })
        return JsonResponse({
            "success": False,
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid data",
            "errors": serializer.errors
        })



    @csrf_exempt
    def deleteTaskData(self, request):
        task_id = request.data.get('task_id')
        try:
            task = TemplateTaskList.objects.get(id=task_id)
        except TemplateTaskList.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Checklist not found",
            })

        task.delete()
        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "Checklist deleted successfully",
        })
