

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from digielves_setup.models import GmailAuth, GmailEmail, User
from employee.seriallizers.social_media.gmail_auth_seriallizers import GetGmailAuthSerializer, GetGmailEmailSerializer, GmailAuthSerializer
from employee.seriallizers.social_media.meta_auth_seriallizers import GetMetaAuthSerializer, MetaAuthSerializer, PutMetaAuthSerializer

from rest_framework import status
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

class GmailAuthViewSet(viewsets.ModelViewSet):

    serializer_class = MetaAuthSerializer
    


    @csrf_exempt
    def AddGmailAuth(self, request):
        try:
            user_id = request.data.get('user_id')
            platform = request.data.get('platform')

            existing_auth = GmailAuth.objects.filter(user_id=user_id, platform=platform).first()

            
            mutable_data = request.data.copy()
            
            mutable_data['status_login'] = True

            if existing_auth:
                serializer = GmailAuthSerializer(existing_auth, data=mutable_data)
            else:
                serializer = GmailAuthSerializer(data=mutable_data)

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
    def get_auth_by_user_gmail(self, request):
        try:
            user_id = request.GET.get('user_id')
            platform = request.GET.get('platform')
            
            GmailAuth_data = GmailAuth.objects.filter(user_id=user_id, platform=platform)
            serializer = GetGmailAuthSerializer(GmailAuth_data, many=True)
            
            # Assuming there will be only one item in the queryset, you can directly take the first item.
            if serializer.data:
                data_item = serializer.data[0]
                data_item['expires_at'] = int(data_item['expires_at']) if data_item['expires_at'].isdigit() else data_item['expires_at']
                data_item['expires_in'] = int(data_item['expires_in']) if data_item['expires_in'].isdigit() else data_item['expires_in']
    
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
        except GmailAuth.DoesNotExist:
            return JsonResponse({'message': 'User not found'}, status=404)
        
    @csrf_exempt
    def update_status_login(self,request):
        try:
            user_id = request.data.get('user_id')
            platform = request.data.get('platform')

            
            existing_auth = GmailAuth.objects.filter(user_id=user_id, platform=platform).first()

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



class GmailEmailViewSet(viewsets.ModelViewSet):
    
    @csrf_exempt
    def add_email(self, request):


        user_id = request.POST.get('user_id')
        email = request.POST.get('email')

        if not user_id or not email:
            return JsonResponse({
                "success": False,
                "status": 400,
                "message": "Missing user_id or email."
            }, status=400)

        try:
            user= User.objects.get(id = user_id)
            # Validate email format
            validate_email(email)
            
            if GmailEmail.objects.filter(email=email).exists():
                return JsonResponse({
                    "success": True,

                })

            # Update or create the GmailEmail record
            GmailEmail.objects.create(user_id=user, email = email)

            response_data = {
                "success": True
            }
            return JsonResponse(response_data, status=200)

        except ValidationError:
            return JsonResponse({
                "success": False,
                "status": 400,
                "message": "Invalid email format."
            }, status=400)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": "An error occurred: " + str(e)
            }, status=500)
            
    @csrf_exempt
    def get_email(self, request):
        try:
            user_id = request.GET.get('user_id')
            
            gmail_email = GmailEmail.objects.filter(user_id=user_id)
            serializer = GetGmailEmailSerializer(gmail_email, many=True)
            

            response_data = {
                "success": True,

                "data": serializer.data
            }
            
            
            return JsonResponse(response_data)
        except GmailEmail.DoesNotExist:
            return JsonResponse({'message': 'User not found'}, status=404)
