

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from digielves_setup.models import MetaAuth
from employee.seriallizers.social_media.meta_auth_seriallizers import GetMetaAuthSerializer, MetaAuthSerializer, PutMetaAuthSerializer

from rest_framework import status
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from django.core.files import File
import requests
from io import BytesIO
import uuid 


class MetaAuthViewSet(viewsets.ModelViewSet):

    serializer_class = MetaAuthSerializer
    


    @csrf_exempt
    def AddmetaAuth(self, request):
        try:
            user_id = request.data.get('user_id')
            meta_platform = request.data.get('metaplatform')
            
            
            existing_auth = MetaAuth.objects.filter(user_id=user_id, metaplatform=meta_platform).first()

            mutable_data = request.data.copy()
            
            mutable_data['status_login'] = True
            
            if existing_auth:
                
                serializer = MetaAuthSerializer(existing_auth, data=mutable_data)
            else:
                serializer = MetaAuthSerializer(data=mutable_data)

            if 'profile_picture' in request.FILES:
                serializer.is_valid(raise_exception=True)
                
                serializer.validated_data['profile_picture'] = request.FILES['profile_picture']
            
            profile_picture_url = request.data.get('profile_picture_url')
            if profile_picture_url:
                
                try:
                    response = requests.get(profile_picture_url)
                    response.raise_for_status() 
                    unique_filename = str(uuid.uuid4()) +'.jpeg' 

                    user_folder = settings.MEDIA_ROOT 

                    
                    save_path = user_folder + '/employee/meta/fb/'

                
                    with open(save_path + unique_filename, 'wb') as image_file:
                        image_file.write(response.content)
                    serializer.is_valid(raise_exception=True)
                    
                    serializer.validated_data['profile_picture'] = '/employee/meta/fb/' + unique_filename
                except Exception as e:
                    pass
#                    response_data = {
#                        "success": False,
#                        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
#                        "message": "An error occurred while processing the image URL.",
#                        "errors": str(e)
#                    }
#                    return JsonResponse(response_data)


            if serializer.is_valid():
                auth = serializer.save()
                user_folder = settings.MEDIA_ROOT 
                if 'profile_picture' in request.FILES:
                    profile = request.FILES['profile_picture']
                    filename = '/employee/meta/fb' + profile.name
                    

                    try:
                        with open(user_folder + filename, 'wb') as f:
                            f.write(profile.read())
                        
                        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
                        filename = fs.save(profile.name, profile)
                        auth.profile_picture = os.path.join('/employee/meta/fb/', filename) 
                    except Exception as e:
                        response_data = {
                            "success": False,
                            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "message": "An error occurred while saving the profile picture.",
                            "errors": str(e)
                        }
                        return JsonResponse(response_data)
                
                profile_url = request.data.get('profile_picture_url')
                if profile_url:

                    
                    try:
                        
                        response = requests.get(profile_url)
                        response.raise_for_status() 
                        unique_filename = str(uuid.uuid4())
                        
                        user_folder = settings.MEDIA_ROOT
                        
                        save_path =user_folder+ '/employee/meta/fb'

                        
                        with open(save_path + unique_filename, 'wb') as image_file:
                            image_file.write(response.content)

                    except Exception as e:
                        pass
#                        response_data = {
#                            "success": False,
#                            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
#                            "message": "An error occurred while processing the image URL.",
#                            "errors": str(e)
#                        }
#                        return JsonResponse(response_data)

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
    def get_user_meta_auth(self,request):
        user_id = request.GET.get('user_id')
        metaplatform = request.GET.get('metaplatform')
        

        if user_id:
        
            if metaplatform == "Facebook":
                fb_auth = MetaAuth.objects.filter(user_id=user_id,metaplatform="Facebook").last()
                if fb_auth:
                    response_data = {
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "User Facebook Auth Details",
                    "data": {
                        "meta_auth": {
                            "status_login": fb_auth.status_login
                            }
                        }
                    }
                else:
                    response_data = {
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "User Facebook Auth Details",
                    "data": {
                        "meta_auth": {
                            "status_login": False
                            }
                        }
                    }
    
                return JsonResponse(response_data)
            if metaplatform == "Instagram":
                 ig_auth = MetaAuth.objects.filter(user_id=user_id,metaplatform="Instagram").last()
                 
                 if ig_auth:
                    response_data = {
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "User Instagram Auth Details",
                    "data": {
                        "meta_auth": {
                            "status_login": ig_auth.status_login
                            }
                        }
                    }
                 else:
                      response_data = {
                      "success": True,
                      "status": status.HTTP_200_OK,
                      "message": "User Instagram Auth Details",
                      "data": {
                          "meta_auth": {
                              "status_login": False
                              }
                          }
                      }
                 return JsonResponse(response_data)

        else:
            return JsonResponse({
                "success": False,
                "message": "user_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        
    
    @csrf_exempt
    def get_auth_by_user_meta(self,request):
        try:
            user_id = request.GET.get('user_id')
            meta_platform = request.GET.get('meta_platform')

            
            metaAuth_data = MetaAuth.objects.filter(user_id=user_id, metaplatform=meta_platform)
            serializer = GetMetaAuthSerializer(metaAuth_data, many=True)

            response_data = {
            "success": True,
            "status": 200,
            "message": "Data retrieved successfully",
            "data": serializer.data
        }
        
            
            return JsonResponse(response_data)
        except MetaAuth.DoesNotExist:
            return JsonResponse({'message': 'User not found'}, status=404)


    @csrf_exempt
    def update_meta_auth(self,request):
        try:
            user_id = request.data.get('user_id')
            meta_platform = request.data.get('metaplatform')

            try:
                auth = MetaAuth.objects.get(user_id=user_id, metaplatform=meta_platform)
            except MetaAuth.DoesNotExist:
                response_data = {
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Authentication entry not found for the user."
                }
                return JsonResponse(response_data, status=status.HTTP_404_NOT_FOUND)

            serializer = PutMetaAuthSerializer(auth, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()

                if 'profile_picture' in request.FILES:
                    profile = request.FILES['profile_picture']
                    filename = '/employee/meta/fb' + profile.name
                    user_folder = settings.MEDIA_ROOT 

                    try:
                        with open(user_folder + filename, 'wb') as f:
                            f.write(profile.read())
                        
                        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
                        filename = fs.save(profile.name, profile)
                        auth.profile_picture = os.path.join('/employee/meta/fb/', filename) 
                        auth.save()
                    except Exception as e:
                        response_data = {
                            "success": False,
                            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "message": "An error occurred while saving the profile picture.",
                            "errors": str(e)
                        }
                        return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                response_data = {
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Data updated successfully.",
                    "data": serializer.data
                }
                return JsonResponse(response_data)
            else:
                response_data = {
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to update data.",
                    "errors": serializer.errors
                }
                return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response_data = {
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred while processing your request.",
                "errors": str(e)
            }
            return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
    @csrf_exempt
    def update_status_login(self,request):
        try:
            user_id = request.data.get('user_id')
            metaplatform = request.data.get('metaplatform')

            
            existing_auth = MetaAuth.objects.filter(user_id=user_id, metaplatform=metaplatform).first()

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



        