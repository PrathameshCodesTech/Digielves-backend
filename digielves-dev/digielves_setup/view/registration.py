import csv
import datetime
import json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from digielves_setup.models import User, UserCreation

# Authentication Modules for rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.permissions import  IsAuthenticated ,AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
from rest_framework.throttling import AnonRateThrottle,UserRateThrottle
from digielves_setup.seriallizers.user import AddAdminSerializer, UserRegistraionSerializer, UpdateUserRegistraionSerializer, UserShowSerializer

import bcrypt
from django.http import JsonResponse,HttpResponse
from rest_framework import status

import gzip
from django.views.decorators.gzip import gzip_page
from django.middleware.gzip import GZipMiddleware

from digielves_setup.validations import is_valid_password


from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# Create your views here.
class Registration(viewsets.ModelViewSet):

    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle,UserRateThrottle]

    serializer_class = UserRegistraionSerializer

    # Client Registration API 
    @csrf_exempt
    def UpdateUserRegistraion(self,request):
        print(request.data)
        
        
        with open('useful.csv') as f:
            reader = csv.reader(f)
            next(reader)      # <- skip the header row
            for row in reader:
                csv_key = row[0]
                
        csv_key = csv_key.replace('RUSH','')
        csv_key = csv_key.replace('ISHK','')

        

        try:
            user_object=User.objects.get(id = request.data['user_id'])
            create_user = UserCreation.objects.get(organization_id = request.data['organization_id'])
            
            try:
                is_valid_password(request.data['password'])
                user_object.password= bcrypt.hashpw(request.data['password'].encode('utf-8')  , csv_key.encode('utf-8') )
            except:
                pass 
            
            user = UpdateUserRegistraionSerializer(user_object,data=request.data)
            if user.is_valid(raise_exception=True):
                try:    
                    response = user.save()
                    # print(response.id)
                    create_user.processed = 1
                    create_user.employee_user_id = response.id
                    create_user.save()
                    
                    token= RefreshToken.for_user(User.objects.get(id=response.id))
                    
                    token_json = {'access' :{} , 'refresh' : {}}
                    token_json['access']['token'] = str(token.access_token) 
                    token_json['refresh']['token'] = str(token)

                    
                    decoded_token = RefreshToken(str(token)).payload
                    expiry_time = decoded_token["exp"]
                    # Convert the expiry time to a datetime object
                    token_json['refresh']['expiry'] = datetime.datetime.fromtimestamp(expiry_time)
                    
                    
                    decoded_token = AccessToken(str(token.access_token)).payload
                    expiry_time = decoded_token["exp"]
                    # Convert the expiry time to a datetime object
                    token_json['access']['expiry'] = datetime.datetime.fromtimestamp(expiry_time)
                    
                    
                    return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "Partner created successfully",
                    'token': token_json,

                    "data": {
                        'user_id' : user_object.id
                    }
                    })  
                        
                except Exception as e:
                    # print(e)
                    return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST, 
                            "message": "Failed to register user",
                            "errors": str(e)
                            })   
                            
            else:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to register user",
                        "errors": str(user.error)
                        })   
                
                
        except Exception as e:
            return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to register user",
                        "errors": str(e)
                        })



    # Client Registration API 
    @csrf_exempt
    def UserRegistraion(self,request):
        print(request.data)
        print("----------hmm")
        user_object=User()
        
        with open('useful.csv') as f:
            reader = csv.reader(f)
            next(reader)      # <- skip the header row
            for row in reader:
                csv_key = row[0]
                
        csv_key = csv_key.replace('RUSH','')
        csv_key = csv_key.replace('ISHK','')

        

        try:
            create_user = UserCreation.objects.get(token = request.data['token'], organization_id = request.data['organization_id'] )
            #, processed = 0
            user = self.serializer_class(user_object,data=request.data)

            if user.is_valid(raise_exception=True):
                try:    
                    response = user.save()
                    # print(response.id)
                    
                    create_user.processed = 1
                    create_user.employee_user_id = response.id
                    create_user.save()
                    
                    token= RefreshToken.for_user(User.objects.get(id=response.id))
                    
                    token_json = {'access' :{} , 'refresh' : {}}
                    token_json['access']['token'] = str(token.access_token) 
                    token_json['refresh']['token'] = str(token)

                    
                    decoded_token = RefreshToken(str(token)).payload
                    expiry_time = decoded_token["exp"]
                    # Convert the expiry time to a datetime object
                    token_json['refresh']['expiry'] = datetime.datetime.fromtimestamp(expiry_time)
                    
                    
                    decoded_token = AccessToken(str(token.access_token)).payload
                    expiry_time = decoded_token["exp"]
                    # Convert the expiry time to a datetime object
                    token_json['access']['expiry'] = datetime.datetime.fromtimestamp(expiry_time)
                    
                    
                    return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User created successfully",
                    'token': token_json,

                    "data": {
                        'user_id' : user_object.id
                    }
                    })  
                        
                except Exception as e:
                    # print(e)
                    return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST, 
                            "message": "Failed to register user",
                            "errors": str(e)
                            })   
                            
            else:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to register user",
                        "errors": str(user.error)
                        })   
                
                
        except Exception as e:
            return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to register user",
                        "errors": str(e)
                        })



    def delete_user(self,request):
        user_id = request.GET.get('user_id')
    
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                user.delete()
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "User deleted successfully"
                })
            except User.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "message": "User not found with the provided user_id"
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return JsonResponse({
                "success": False,
                "message": "user_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)



    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('user_id', openapi.IN_QUERY, description="Parameter user_id", type=openapi.TYPE_INTEGER,default=2),
    ]) 
    @csrf_exempt
    def getUserData(self,request):
            
        create_user = User.objects.filter(id = request.GET.get('user_id'))
        serializer = UserShowSerializer(create_user, many=True)
        details = json.loads(json.dumps(serializer.data))



        return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,                
                "message": "User Details",
                "data" : {
                    "profile_details" : details,
                    
                }
                
               
                }) 
        
        
    
    @csrf_exempt
    def AdminRegistration(self,request):
        try:
            with open('useful.csv') as f:
                reader = csv.reader(f)
                next(reader)  # Skip the header row

                for row in reader:
                    csv_key = row[0]

            csv_key = csv_key.replace('RUSH', '').replace('ISHK', '')

            user_serializer = AddAdminSerializer(data=request.data)
            
            if user_serializer.is_valid(raise_exception=True):
                try:
                    is_valid_password(request.data['password'])
                    hashed_password = bcrypt.hashpw(request.data['password'].encode('utf-8'), csv_key.encode('utf-8'))
                    user_serializer.validated_data['password'] = hashed_password
                except Exception as e:
                    print(f"Password hashing failed: {e}")

                response = user_serializer.save()

                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Admin created successfully",
                    "data": {
                        'user_id': response.id
                    }
                })

        except FileNotFoundError:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "CSV file not found",
                "data": {}
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"An error occurred: {str(e)}",
                "data": {}
            }) 
            
    
    @csrf_exempt
    def DecodePassword(self,request):
        
        encoded_password = request.data.get('encoded_password', None)

        if encoded_password:
            try:
                hashed_password_bytes = encoded_password.encode('utf-8')

                decoded_password = bcrypt.checkpw(b'password_to_check', hashed_password_bytes)
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Password decoded successfully",
                    "data": {
                        'decoded_password': decoded_password
                    }
                })
            except Exception as e:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": f"An error occurred: {str(e)}",
                    "data": {}
                })
        else:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Encoded password is required",
                "data": {}
            })

