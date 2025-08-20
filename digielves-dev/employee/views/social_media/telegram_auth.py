
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from digielves_setup.models import  TeleUser, TelegramAuth, User

from employee.seriallizers.social_media.telegram_auth_seriallizers import TeleUserSerializer, TelegramAuthSerializer

from employee.views.social_media.telegram_logic.telegram_get_msg_logic import get_messages
from employee.views.social_media.telegram_logic.telegram_logic import handle_telegram_login
from employee.views.social_media.telegram_logic.telegram_msg_logic import handle_telegram_msg


from rest_framework import status
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import asyncio
import time
from telethon.sync import TelegramClient
import threading

# api_id = "28614634"
# api_hash = "254e0027c5ff5e1466217eb7f7730f4d"


class TelegramAuthViewSet(viewsets.ModelViewSet):

    serializer_class = TelegramAuthSerializer
    


    


    @csrf_exempt
    def create_telegram_auth(self, request):
        try:
            user_id = request.data.get('user_id')
            mobile_number = request.data.get('mobile_number')
    
            session_file = os.path.join(settings.MEDIA_ROOT, 'employee', 'telegram', 'user_session', f'{mobile_number}.session')
            if os.path.exists(session_file):
                os.remove(session_file)
    
            print(user_id)
            print(mobile_number)
    
            existing_auth = TelegramAuth.objects.filter(user_id=user_id, mobile_number=mobile_number).first()
    
            if existing_auth is None:
                user = User.objects.get(id=user_id)
                new_auth = TelegramAuth(user_id=user, mobile_number=mobile_number, otp=None, status_login=True)
                serializer = TelegramAuthSerializer(new_auth, data=request.data)
            else:
                serializer = TelegramAuthSerializer(existing_auth, data=request.data)
    
            if serializer.is_valid():
                print("serializer valid")
                auth = serializer.save()
                auth.otp = None
                auth.save()
    
                api_id = "28614634"
                api_hash = "254e0027c5ff5e1466217eb7f7730f4d"
    
                # session = f"{save_path}/{mobile_number}"
    
                login_successful, login_error = asyncio.run(handle_telegram_login(user_id, api_id, api_hash, mobile_number))
    
                if login_successful:
                    existing_auth = new_auth if existing_auth is None else existing_auth
                    existing_auth.status_login = True
                    existing_auth.otp = None
                    existing_auth.save()
    
                    response_data = {
                        "success": True,
                        "status": status.HTTP_201_CREATED,
                        "message": "Login successful.",
                        "data": TelegramAuthSerializer(existing_auth).data  # Serialize the existing_auth
                    }
                    return JsonResponse(response_data, status=status.HTTP_201_CREATED)
                else:
                    session_file = os.path.join(settings.MEDIA_ROOT, 'employee', 'telegram', 'user_session', f'{mobile_number}.session')
                    if os.path.exists(session_file):
                        os.remove(session_file)
    
                    response_data = {
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Login unsuccessful.",
                        "errors": login_error
                    }
    
                    return JsonResponse(response_data)
            else:
                response_data = {
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create/update data.",
                    "errors": serializer.errors
                }
                return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)
    
        except Exception as e:
            print("-------------------------------exception 124")
            print(e)
    
            response_data = {
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred while processing your request.",
                "errors": str(e)
            }
            return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        

    @csrf_exempt
    def add_otp(self,request):
        try:
            user_id = request.data.get('user_id')
            mobile = request.data.get('mobile_number')

            
            existing_auth = TelegramAuth.objects.filter(user_id=user_id, mobile_number=mobile).first()

            if existing_auth:
            
                serializer = TelegramAuthSerializer(existing_auth, data=request.data)
            else:
                
                serializer = TelegramAuthSerializer(data=request.data)

            if serializer.is_valid():
                auth = serializer.save()
                response_data = {
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Data created successfully.",
                    "data": serializer.data
                }
                return JsonResponse(response_data, status=status.HTTP_201_CREATED)
            else:
                response_data = {
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create/update data.",
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
            mobile = request.data.get('mobile_number')
            platform = request.data.get('platform')
            session_file = os.path.join(settings.MEDIA_ROOT, 'employee', 'telegram', 'user_session', f'{mobile}.session')
            if os.path.exists(session_file):
                os.remove(session_file)


            session_file1 = os.path.join(settings.MEDIA_ROOT, 'employee', 'telegram', 'user_session', f'{mobile}.session-journal')
            if os.path.exists(session_file1):
                os.remove(session_file1)
            

            
            existing_auth = TelegramAuth.objects.filter(mobile_number=mobile, platform=platform).first()

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
            
        
        
    @csrf_exempt
    def get_user_telegram_auth(self,request):
        user_id = request.GET.get('user_id')

        if user_id:
            # Filter TelegramAuth records by user_id
            telegram_auth = TelegramAuth.objects.filter(user_id=user_id).last()
    
            if telegram_auth:
                response_data = {
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "User Telegram Auth Details",
                    "data": {
                        "telegram_auth": {
                            "status_login": telegram_auth.status_login,
                            "mobile_number": telegram_auth.mobile_number,
                        }
                    }
                }
    
                return JsonResponse(response_data)
            else:
                return JsonResponse({
                    "success": True,
                    "message": "No Telegram Auth data found for the provided user_id",
                    "data": {
                        "telegram_auth": {
                            "status_login":False,
                            "mobile_number": "",
                     }}
                })
        else:
            return JsonResponse({
                "success": False,
                "message": "user_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        



class TelegramUserViewSet(viewsets.ModelViewSet):

    serializer_class = TeleUserSerializer
    @csrf_exempt
    def Add_user(self, request):
        try:
            serializer = TeleUserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()

                response_data = {
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Data created successfully.",
                    "data": serializer.data
                }
                
                return JsonResponse(response_data, status=status.HTTP_201_CREATED)
            

            response_data = {
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create",
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
            return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    

    @csrf_exempt
    def delete_username(self, request):
        mobile_number = request.GET.get('mobile_number')
        username = request.GET.get('username')

        try:
            teleuser = TeleUser.objects.get(telegram_auth=mobile_number, username=username)

            # Delete the record
            teleuser.delete()

            response_data = {
                "success": True,
                "status": status.HTTP_204_NO_CONTENT,
                "message": "Data deleted successfully.",
            }
            return JsonResponse(response_data, status=status.HTTP_204_NO_CONTENT)

        except TeleUser.DoesNotExist:
            response_data = {
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "TeleUser not found.",
            }
            return JsonResponse(response_data, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            response_data = {
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred while processing your request.",
                "errors": str(e)
            }
            return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @csrf_exempt
    def get_user(self,request):
        try:

            telegram_auth_id = request.GET.get('mobile_number')
            
            if telegram_auth_id is not None:
                try:
                    # Retrieve all usernames associated with the provided telegram_auth_id
                    usernames = TeleUser.objects.filter(telegram_auth=telegram_auth_id).values_list('username', flat=True)

                    response_data = {
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "message": "Usernames retrieved successfully.",
                        "data": [{"username": username} for username in usernames],
                    
                    }
                    return JsonResponse(response_data, status=status.HTTP_200_OK)

                except Exception as e:
                    response_data = {
                        "success": False,
                        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": "An error occurred while processing your request.",
                        "errors": str(e)
                    }
                    return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                response_data = {
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Please provide the 'telegram_auth' parameter.",
                }
                return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
                response_data = {
                    "success": False,
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "An error occurred while processing your request.",
                    "error":True,
                    "errors": str(e)
                }
                return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        

    

class TelegramMessageViewSet(viewsets.ModelViewSet):

    def send_telegram_message(self,request):
        try:
            mobile_number = request.data.get('mobile_number')
            mobile_number_or_username = request.data.get('mobile_number_or_username')
            message = request.data.get('message')

            print(mobile_number)
            print(mobile_number_or_username)
            print(message)
            
            # Check if session file exists
            session_file = os.path.join(settings.MEDIA_ROOT, 'employee', 'telegram', 'user_session', f'{mobile_number}.session')
            print(session_file)
            
            if not os.path.exists(session_file):
                response_data = {
                    "success": False,
                    "status": 400,
                    "message": "Not logged in. Session file not found.",
                    "errors": None
                }
                return JsonResponse(response_data, status=400)
            
            # Use Telegram API to send message
            api_id = "28614634"
            api_hash = "254e0027c5ff5e1466217eb7f7730f4d"


            result = asyncio.run(handle_telegram_msg(api_id, api_hash, mobile_number_or_username, session_file, message))

            if result:
                response_data = {
                    "success": True,
                    "status": 200,
                    "message": "Message sent successfully.",
                    "errors": None
                }
            else:
                response_data = {
                    "success": False,
                    "status": 400,
                    "message": "Failed to send the message.",
                    "errors": None
                }

            return JsonResponse(response_data, status=response_data["status"])
        except Exception as e:
                response_data = {
                    "success": False,
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "An error occurred while processing your request.",
                    "errors": str(e)
                }
                return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    def get_telegram_message(self,request):
        try:
            mobile_number = request.GET.get('mobile_number')
            mobile_number_or_username = request.GET.get('mobile_number_or_username')

            print(mobile_number)
            print(mobile_number_or_username)
            
            
            # Check if session file exists
            session_file = os.path.join(settings.MEDIA_ROOT, 'employee', 'telegram', 'user_session', f'{mobile_number}.session')
            print(session_file)
            
            if not os.path.exists(session_file):
                response_data = {
                    "success": False,
                    "status": 400,
                    "message": "Not logged in. Session file not found.",
                    "errors": None
                }
                return JsonResponse(response_data, status=400)
            
            # Use Telegram API to send message
            api_id = "28614634"
            api_hash = "254e0027c5ff5e1466217eb7f7730f4d"


            result = asyncio.run(get_messages(api_id, api_hash, mobile_number_or_username, session_file))
            print("----------result----------")
            print(result)

            if result:
                response_data = {
                    "success": True,
                    "status": 200,
                    "message_data": result,
                    "message": "Message sent successfully.",
                    "errors": None
                }
            elif result == []:
                response_data = {
                    "success": True,
                    "status": 200,
                    "message_data": [],
                    "message": "Message sent successfully.",
                    "errors": None
                }

            else:
                response_data = {
                    "success": False,
                    "status": 400,
                    "message": "Failed to get the message.",
                    "error":True,
                    "errors": None
                }

            return JsonResponse(response_data, status=response_data["status"])

        except Exception as e:
                response_data = {
                    "success": False,
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "An error occurred while processing your request.",
                    "error":True,
                    "errors": str(e)
                }
                return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        