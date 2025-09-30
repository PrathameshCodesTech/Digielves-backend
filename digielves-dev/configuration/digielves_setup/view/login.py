  # Django Required Dependencies
# from gzip import compress
from django.shortcuts import render
from configuration.gzipCompression import compress
from digielves_setup.models import User, UserCreation
from digielves_setup.seriallizers.user import UserLoginSeriallizer
from rest_framework import viewsets
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page

from rest_framework import status


# Authentication Modules for rest Framework
from rest_framework.permissions import  IsAuthenticated ,AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
from rest_framework.throttling import AnonRateThrottle,UserRateThrottle

import base64
import json

#for qr code generation

import csv
import bcrypt
import datetime

import base64
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


# Application Response Serializer


from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from rest_framework.generics import GenericAPIView
from django.core.cache import cache
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from configuration.send_otp import sendMailOtp,sendMobileOtp
 
import random


@method_decorator(csrf_exempt, name='dispatch')
class LogInClass(viewsets.ModelViewSet):
    print('idher pucha')
    # authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]
    print('trying here')
    throttle_classes = [AnonRateThrottle,UserRateThrottle]

    serializer_class = UserLoginSeriallizer



    # Client Registration API 
    def logIn(self,request):
        print("=== LOGIN DEBUG START ===")
        print(f"Request method: {request.method}")
        print(f"Request content type: {request.content_type}")
        print(f"Request data: {request.data}")
        print(f"Request POST: {request.POST}")
        print(f"Request body: {request.body}")
        print("=== LOGIN DEBUG END ===")
        try:
            with open('useful.csv') as f:
                reader = csv.reader(f)
                next(reader)      # <- skip the header row
                for row in reader:
                    csv_key = row[0]

            csv_key = csv_key.replace('RUSH','')
            csv_key = csv_key.replace('ISHK','')
            # print(fernet)
            user_password = bcrypt.hashpw(request.data['password'].encode('utf-8')  , csv_key.encode('utf-8') ) 

            user = User.objects.get( email=request.data['email'], password= user_password )

            token= RefreshToken.for_user(User.objects.get(id=user.id))
            print("Token Details")
            
            
            print(user.id)
            create_user = UserCreation.objects.get(user_id = user.id )

            token_json = {'access' :{} , 'refresh' : {}}
            token_json['access']['token'] = str(token.access_token) 
            token_json['refresh']['token'] = str(token)

            
            decoded_token = RefreshToken(str(token)).payload
            print(decoded_token)
            expiry_time = decoded_token["exp"]
            # Convert the expiry time to a datetime object
            token_json['refresh']['expiry'] = str(datetime.datetime.fromtimestamp(expiry_time))
            
            
            decoded_token = AccessToken(str(token.access_token)).payload
            expiry_time = decoded_token["exp"]
            # Convert the expiry time to a datetime object
            token_json['access']['expiry'] = str(datetime.datetime.fromtimestamp(expiry_time))

            
            response = {
            "success": True,
            "status": status.HTTP_200_OK,                
            "message": "Log-in successfully",
            'token': token_json,
            "data": {
                'user_id' : user.id,
                'user_role' : user.user_role,
                'verified' : user.verified,
                'processed' : create_user.processed

            },
            "registration_token":  "create_user.token"
                
            }
            # response.set_cookie('jwt_token', token, httponly=True)

            return compress(response)   
        except Exception as e:
            response = {
            "success": False,
            "status": status.HTTP_400_BAD_REQUEST,                
            "message": "Incorrect Login ID or Password",
                        "errors": str(e)
            }
            
            return compress(response)   

    def forgetPassword(self,request):
        try:

            

            user = User.objects.get( email=request.data['email'] )

            with open('useful.csv') as f:
                reader = csv.reader(f)
                next(reader)      # <- skip the header row
                for row in reader:
                    csv_key = row[0]

            csv_key = csv_key.replace('RUSH','')
            csv_key = csv_key.replace('ISHK','')
            # print(fernet)
            
            user_password = bcrypt.hashpw(request.data['password'].encode('utf-8')  , csv_key.encode('utf-8') ) 
            user.password = user_password
            user.save()
            

            
            response = {
            "success": True,
            "status": status.HTTP_200_OK,                
            "message": "Password changed successfully",
            "data": {
                'user_id' : user.id
            }
            }
            return compress(response)  
        
        except Exception as e:
            response = {
            "success": False,
            "status": status.HTTP_400_BAD_REQUEST,                
            "message": "Incorrect details",
            "errors": str(e)
            }
            
            return compress(response)   
     


    def send_otp(self,request):


        try:
            otp = random.randint(100000, 999999)

            if '@' in request.data['email']:
                email = request.data['email']
                sendMailOtp(request.data['email'], otp)
            else:
                sendMobileOtp(request.data['email'], otp)

            
            
            cache.set(f'otp:{str(email)}', otp, timeout=120)
            response = {
            "success": True,
            "status": status.HTTP_200_OK,                
            "message": "OTP sent  successfully",

            }
            return compress(response)  
        except Exception as e:
            response = {
            "success": False,
            "status": status.HTTP_400_BAD_REQUEST,                
            "message": "Incorrect details",
                        "errors": str(e)
            }
            
            return compress(response)
        

    def otpVerification(self,request):

        try:
            email = request.data['email']
            entered_otp = ''.join(request.data['otp'])
            print(entered_otp)
            cached_otp = cache.get(f'otp:{str(email)}')
            print(cached_otp)
            if str(entered_otp) == str(cached_otp):
              
            
                response = {
                "success": True,
                "status": status.HTTP_200_OK,                
                "message": "OTP Verified",

                }
                return compress(response)
            else:
                print("this---")
                response = {
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,                
                "message": "Incorrect details",
                
                }  
                return compress(response)
              
              
        except Exception as e:
            response = {
            "success": False,
            "status": status.HTTP_400_BAD_REQUEST,                
            "message": "Incorrect details",
                        "errors": str(e)
            }
            
            return compress(response)  

    

    def sendLoginOtp(self,request):


        try:
            otp = random.randint(100000, 999999)

            if '@' in request.data['email']:
                user = User.objects.get( email=request.data['email'] )
                sendMailOtp(request.data['email'], otp)
            else:
                user = User.objects.get( phone_no=request.data['email']  )
                sendMobileOtp(request.data['email'], otp)

            
            
            cache.set(f'otp:{user.id}', otp, timeout=120)
            response = {
            "success": True,
            "status": status.HTTP_200_OK,                
            "message": "OTP sent  successfully",

            }
            return compress(response)  
        except Exception as e:
            response = {
            "success": False,
            "status": status.HTTP_400_BAD_REQUEST,                
            "message": "Incorrect details",
                        "errors": str(e)
            }
            
            return compress(response)
        


    def loginOtpVerification(self,request):


        
        try:
            user = User.objects.get( email=request.data['email']  )
            entered_otp = request.data['otp']
            print(entered_otp)
            cached_otp = cache.get(f'otp:{user.id}')
            print(cached_otp)
            if str(entered_otp) == str(cached_otp):
                # OTP is valid
                token= RefreshToken.for_user(user)
                
                print(user.id)
                create_user = UserCreation.objects.get(user_id = user.id )

                print()
                token_json = {'access' :{} , 'refresh' : {}}
                token_json['access']['token'] = str(token.access_token) 
                token_json['refresh']['token'] = str(token)

                
                decoded_token = RefreshToken(str(token)).payload
                expiry_time = decoded_token["exp"]
                # Convert the expiry time to a datetime object
                token_json['refresh']['expiry'] = str(datetime.datetime.fromtimestamp(expiry_time))
                
                
                decoded_token = AccessToken(str(token.access_token)).payload
                expiry_time = decoded_token["exp"]
                # Convert the expiry time to a datetime object
                token_json['access']['expiry'] = str(datetime.datetime.fromtimestamp(expiry_time))
                
            
                response = {
                "success": True,
                "status": status.HTTP_200_OK,                
                "message": "OTP Verified",
                "token" : token_json,
                'processed' : create_user.processed


                }
                return compress(response)
            else:
                print("this---")
                response = {
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,                
                "message": "Incorrect details",
                
                }  
                return compress(response)
              
              
        except Exception as e:
            response = {
            "success": False,
            "status": status.HTTP_400_BAD_REQUEST,                
            "message": "Incorrect details",
                        "errors": str(e)
            }
            
            return compress(response)  


