
from django.http import JsonResponse
from admin_app.seriallizers.task_seriallizers import OrgDetailsSerializer, TasksSerializerAdmin

from configuration.gzipCompression import compress
from digielves_setup.models import OrganizationDetails, TaskHierarchy, Tasks, User
from admin_app.seriallizers.task_seriallizers import TasksSerializerAdmin

from configuration.gzipCompression import compress
from digielves_setup.models import Tasks, User

from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt

from rest_framework import serializers

# import datetime
from django.contrib.contenttypes.models import ContentType
from django.core.serializers import serialize
from django.shortcuts import get_object_or_404

from rest_framework import status
from django.http import HttpResponse
from openpyxl import Workbook
import pandas as pd
import io
from django.db.models.functions import Length
from django.db.models import F, Func, Value
from django.utils import timezone
from datetime import datetime
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache

class Replace(Func):
    function = 'REPLACE'
    
    
    
class CustomPagination(PageNumberPagination):
    page_size = 10  # Number of tasks per page
    page_size_query_param = 'page_size'
    max_page_size = 1000
    
class AdminTaskViewSet(viewsets.ModelViewSet):
    
    


    


    @csrf_exempt
    def get_task_excel(self,request):
        user_id = request.GET.get('user_id')
         

        try:
            user_check = User.objects.filter(id=user_id, user_role='Dev::Admin').first()
            print(user_check)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": "You don't have permission"
            })

        try:
            all_tasks = Tasks.objects.filter(is_personal=False, inTrash=False)
            serialize = TasksSerializerAdmin(all_tasks, many=True)

            # Convert data to pandas DataFrame
            df = pd.json_normalize(serialize.data, sep='_')

            # Create an Excel writer
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Task List')

                # Get the xlsxwriter workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['Task List']

                # Add grouping (outline) to create a collapsible structure
                max_row = len(df) + 1
                for i in range(max_row):
                    worksheet.set_row(i, None, None, {'level': len(df.iloc[i]['task_topic'].split('.'))} if i < len(df) else {})

            # Create the response with appropriate headers
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="task_list23.xlsx"'
            response.write(excel_buffer.getvalue())

            return response
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to get Task.",
                "errors": str(e)
            })




    @csrf_exempt
    def get_task(self, request):
        user_id = request.GET.get('user_id')
        page = request.GET.get('page', 1)
        try:
            user_check = User.objects.filter(id=user_id, user_role='Dev::Admin').first()
            if not user_check:
                return JsonResponse({
                    "success": False,
                    "message": "You don't have permission"
                })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": "You don't have permission"
            })

        cache_key = f'task_list_{user_id}_page_{page}'
        cached_response = cache.get(cache_key)

        if cached_response:
            formatted_response = {
            "success": True,
            "status": 200,
            "message": "Task List",
            "data": cached_response['data']  # Ensure this key exists
            }
            return JsonResponse(formatted_response)
        try:
            all_task = TaskHierarchy.objects.filter(is_personal=False, inTrash=False, status__isnull=False)
           
            paginator = CustomPagination()
            paginated_tasks = paginator.paginate_queryset(all_task, request)
            
            
            serialized_data = TasksSerializerAdmin(paginated_tasks, many=True).data
            
            response_data = {
                    "success": True,
                    "status": 200,
                    "message": "Task List",
                    "data": serialized_data,
                }
                        
            cache.set(cache_key, response_data, timeout=60*5)  # Cache for 2 minutes
            
            return JsonResponse(response_data)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to get Task.",
                "errors": str(e)
            })

    # @csrf_exempt
    # def get_task(self, request):
    #     user_id = request.GET.get('user_id') 
            
    #     try:
    #         user_check = User.objects.filter(id=user_id,user_role='Dev::Admin').first()
    #     except Exception as e:
        
    #         return JsonResponse({
    #                 "success": False,
    #                 "message": "You dont have permission"
    #                 })
        
    #     try:
    #         all_task = TaskHierarchy.objects.filter(is_personal=False, inTrash=False, status__isnull=False)
            
    #         seriallize=TasksSerializerAdmin(all_task,many=True)
            
    #         response={
    #         "success": True,
    #         "status": status.HTTP_200_OK,                
    #         "message": " Task List",
    #         'data':seriallize.data
    #         }
    #         return compress(response)
    #     except Exception as e:
    #         return JsonResponse({
    #                 "success": False,
    #                 "status": status.HTTP_400_BAD_REQUEST,
    #                 "message": "Failed to get Task.",
    #                 "errors": e
    #             })
            
            
class OrgViewSet(viewsets.ModelViewSet):
    
    @csrf_exempt
    def get_organizations(self, request):
        user_id = request.GET.get('user_id') 
            
        try:
            user_check = User.objects.filter(id=user_id,user_role='Dev::Admin').first()
            print(user_check)
        except Exception as e:
        
            return JsonResponse({
                    "success": False,
                    "message": "You dont have permission"
                    })
        
        try:
            all_org = OrganizationDetails.objects.filter(is_personal=False,inTrash=False)
            
            seriallize=OrgDetailsSerializer(all_org,many=True)
            
            response={
            "success": True,
            "status": status.HTTP_200_OK,                
            "message": " org List",
            'data':seriallize.data
            }
            return compress(response)
        except Exception as e:
            return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to get org.",
                    "errors": e
                })