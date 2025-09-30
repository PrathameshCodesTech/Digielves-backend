from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from digielves_setup.models import OutlookAuth
from employee.seriallizers.social_media.outlook_auth_seriallizers import OutlookAuthSerializer, GetOutlookAuthSerializer

from rest_framework import status
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

class OutlookAuthViewSet(viewsets.ModelViewSet):

    serializer_class = OutlookAuthSerializer
    
    @csrf_exempt
    def AddOutlookAuth(self, request):
        try:
            user_id = request.data.get('user_id')
            
    
            existing_auth = OutlookAuth.objects.filter(user_id=user_id, platform="Outlook").first()
    
            mutable_data = request.data.copy()
            mutable_data['status_login'] = True
    
            if existing_auth:
                serializer = OutlookAuthSerializer(existing_auth, data=mutable_data)
            else:
                serializer = OutlookAuthSerializer(data=mutable_data)
    
            if serializer.is_valid():
                auth = serializer.save()
                auth.save()
                response_data = {
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Data created successfully.",
                    "data": serializer.data
                }
                return JsonResponse(response_data)
            else:
                response_data = {
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create/update data.",
                    "errors": serializer.errors
                }
                return JsonResponse(response_data)
        except Exception as e:
            response_data = {
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred while processing your request.",
                "errors": str(e)
            }
            return JsonResponse(response_data)
            


    @csrf_exempt
    def get_auth_by_user_outlook(self, request):
        try:
            user_id = request.GET.get('user_id')
            
            OutlookAuth_data = OutlookAuth.objects.filter(user_id=user_id)
            serializer = GetOutlookAuthSerializer(OutlookAuth_data, many=True)
            
            
            if serializer.data:

                data_item = serializer.data[0]
    
                response_data = {
                    "success": True,
                    "status": 200,
                    "message": "Data retrieved successfully",
                    "login_status": data_item['status_login'],
                    "data": data_item
                }
            else:
                
                response_data = {
                    "success": True,
                    "status": 200,
                    "message": "No data found",
                    "data": []
                }
            
            return JsonResponse(response_data)
        except OutlookAuth.DoesNotExist:
            return JsonResponse({'message': 'User not found'}, status=404)
            
            
            
    @csrf_exempt
    def update_status_login(self,request):
        try:
            user_id = request.data.get('user_id')
            

            
            existing_auth = OutlookAuth.objects.filter(user_id=user_id).first()

            if existing_auth:
                
                existing_auth.status_login = False
                existing_auth.save()

                response_data = {
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Status login updated successfully.",
                }
                return JsonResponse(response_data)
            else:
                response_data = {
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Authentication record not found for the user and platform.",
                }
                return JsonResponse(response_data)
        except Exception as e:
            response_data = {
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred while processing your request.",
                "errors": str(e),
            }
            return JsonResponse(response_data)
