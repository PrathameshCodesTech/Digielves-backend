import base64
import json
import random
from django.shortcuts import render
from configuration.authentication import JWTAuthenticationUser
from configuration.onboardingEmail import sendMail
from configuration.userCreationToken import generate_random_string
from digielves_setup.models import UserCreation, User
from digielves_setup.seriallizers.user_creation_seriallizer import UserCreationSerializers,UpdateUserCreationSerializers

from rest_framework import viewsets
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status


# Authentication Modules for rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.permissions import  IsAuthenticated ,AllowAny

from django.db.models import Max


from django.db.models import Q

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
# Application Response Serializer 



from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class UserCreationClass(viewsets.ModelViewSet):

    authentication_classes = [JWTAuthenticationUser]
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]

    throttle_classes = [AnonRateThrottle,UserRateThrottle]
    serializer_class= UpdateUserCreationSerializers
    @csrf_exempt
    def createUser(self,request):
        print("dfds")
        userDetails=UserCreation()
        try:
            token = generate_random_string(52)
            userDetails.token = token
            userAddressSerialData = UpdateUserCreationSerializers(userDetails,data=request.data)
            
            try:
                
                if userAddressSerialData.is_valid(raise_exception=True):
                    sendMail(request.data['email'], "https://www.ordinet.in/Digielves%20Project/Employee/index.html?access="+ str(token) + '&org=' + str(request.data['organization_id']))
                    userAddressSerialData.save()

                    return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User Created successfully",
                    "data":
                        {
                            "user_creation_id" : userDetails.id
                        }
                    })        
            except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Create User",
                        "errors": str(e)
                        })
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Create User",
                        "errors": str(e)
                        })
                
                
    @csrf_exempt
    def verifyUser(self,request):
        try:
            
            create_user = UserCreation.objects.get(id = request.data['id'], processed = 2 )
            create_user.verified = 1
            create_user.processed = 3

            create_user.save()
            print("========================")
            print(create_user.user_id_id)

            user = User.objects.get(id=create_user.user_id_id)
            user.verified = 1
            user.save()

            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User Verified successfully",
                    "data":
                        {
                            "user_id" : create_user.user_id_id
                        }
                    }) 
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Create User",
                        "errors": str(e)
                        })
                
             
    @csrf_exempt
    def rejectUser(self,request):
        try:
            
            create_user = UserCreation.objects.get(id = request.data['id'], processed = 2 )
            create_user.verified = 2
            create_user.processed = 3
            create_user.save()
            
            user = User.objects.get(id=create_user.user_id)
            user.verified = 2
            user.save()

            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User Rejected successfully",
                    "data":
                        {
                            "user_id" : create_user.user_id
                        }
                    }) 
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Rejecte User",
                        "errors": str(e)
                        })
          
          
             
    @csrf_exempt
    def verifyDoctor(self,request):
        try:

            
            user = User.objects.get(id=request.data['user_id'])
            user.verified = 1
            user.save()

            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User Verified Successfully",
                    "data":
                        {
                            "user_id" : user.id
                        }
                    }) 
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Verify User",
                        "errors": str(e)
                        })
                

                
                
    @csrf_exempt
    def emailVerification(self,request):
        try:
            
            user = User.objects.get(email = request.data['email'], firstname=  None )


            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "Email Verified Successfully",
                    "data":
                        {
                            "user_id" : user.id
                        }
                    }) 
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Email already in use",
                        "errors": str(e)
                        })
                
    @csrf_exempt
    def isProfileVerified(self,request):
        try:
            
            user = User.objects.get(id= request.data['user_id'], verified = 1)
            

            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User is Verified ",
                    "data":
                        {
                            "user_id" : user.id
                        }
                    }) 
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "User is not Verified ",
                        "errors": str(e)
                        })


    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('user_id', openapi.IN_QUERY, description="Parameter user_id", type=openapi.TYPE_INTEGER,default=2),
    ]) 
    @csrf_exempt
    def getUserData(self,request):
            
        create_user = UserCreation.objects.filter(created_by = request.GET.get('user_id'), verified = 1)
        serializer = UserCreationSerializers(create_user, many=True)
        verified_users = json.loads(json.dumps(serializer.data))
        
        create_user = UserCreation.objects.filter( created_by = request.GET.get('user_id'), verified = 0).exclude(processed = 3)
        serializer = UserCreationSerializers(create_user, many=True)
        processed_users = json.loads(json.dumps(serializer.data))


        return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,                
                "message": "User Details",
                "data" : {
                    "verified_users" : verified_users,
                    "pending_users" : processed_users
                    
                }
                
               
                }) 
            
                
    @csrf_exempt
    def getData(self,request):
            
        create_user = UserCreation.objects.filter().values()
        print(create_user)


        return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,                
                "message": "User Verified successfully",
               
                }) 
    
                
         
                
                
