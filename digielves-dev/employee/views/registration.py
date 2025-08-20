import csv
import datetime
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from configuration.authentication import JWTAuthenticationUser
from digielves_setup.models import User, UserCreation

# Authentication Modules for rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.permissions import  IsAuthenticated ,AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
from rest_framework.throttling import AnonRateThrottle,UserRateThrottle
from digielves_setup.seriallizers.user import UserRegistraionSerializer, UpdateUserRegistraionSerializer

import bcrypt
from django.http import JsonResponse,HttpResponse
from rest_framework import status

import gzip
from django.views.decorators.gzip import gzip_page
from django.middleware.gzip import GZipMiddleware

from digielves_setup.validations import is_valid_password

# Create your views here.
class Registration(viewsets.ModelViewSet):

    # authentication_classes = [JWTAuthenticationUser]
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle,UserRateThrottle]
    

    # Client Registration API 
    serializer_class = UserRegistraionSerializer
    @csrf_exempt
    def UserRegistraion(self,request):
        print("-----vardhanam")
        print(request.data)
        user_object=User()
        
        with open('useful.csv') as f:
            reader = csv.reader(f)
            next(reader)      # <- skip the header row
            for row in reader:
                csv_key = row[0]
                
        csv_key = csv_key.replace('RUSH','')
        csv_key = csv_key.replace('ISHK','')

        try:
            try:
                
                create_user = UserCreation.objects.get(token = request.data['token'], email = request.data['email'] )
            except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": 121, 
                        "message": "No user found with the provided invitation token and email.",
                        })      
     
            #, processed = 0
            user = UserRegistraionSerializer(user_object,data=request.data)


            if user.is_valid(raise_exception=True):
                try:    
                    
                    response = user.save()
                    print("===========================================")
                    print(response.id)
                    print(user_object.id)
                    
                    create_user.processed = 1
                    create_user.employee_user_id = User.objects.get(id=response.id)
                    
                    create_user.save()
                    
                    token= RefreshToken.for_user(User.objects.get(id=response.id))
                    
                    print()
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


# Create your views here.
class UpdateRegistration(viewsets.ModelViewSet):

    # authentication_classes = [JWTAuthenticationUser]
    # permission_classes = [IsAuthenticated]
    # throttle_classes = [AnonRateThrottle,UserRateThrottle]

    serializer_class = UpdateUserRegistraionSerializer

 
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
            print(request.data['token'])
            #print(request.data['organization_id'])
            create_user = UserCreation.objects.get(token = request.data['token'])
            print(create_user)
            
            # , processed = 0 
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
                    create_user.user_id = User.objects.get(id = response.id)
 
                    create_user.save()

                    
                    return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User updated successfully",

                    "data": {
                        'user_id' : user_object.id
                    }
                    })  
                        
                except Exception as e:
                    # print(e)
                    return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST, 
                            "message": "Failed to update user",
                            "errors": str(e)
                            })   
                            
            else:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to update user",
                        "errors": str(user.error)
                        })   
                
                
        except Exception as e:
            return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to update user",
                        "errors": str(e)
                        })

