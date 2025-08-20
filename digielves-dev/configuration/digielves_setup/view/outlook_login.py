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

from configuration.send_otp import sendMailOtp,sendMobileOtp
 
import random
import requests



class OutlookLogInClass(viewsets.ModelViewSet):

    # authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle,UserRateThrottle]

    serializer_class = UserLoginSeriallizer

    def logIn(self,request):
        if True:
            response = requests.get("https://login.microsoftonline.com/ad2b1ce8-b182-443b-bc9c-1db30df9f99e/oauth2/v2.0/authorize?client_id=33d46bb8-945b-4c07-bf6c-74f89c263b23&response_type=code&redirect_uri=https://vibecopilot.ai/employee/settings&response_mode=query&scope=offline_access%20User.Read%20Mail.Read&state=12345")
            
            print(response )
                        

            
            response = {
            "success": True,
            "status": status.HTTP_200_OK,                
            "message": "Password changed successfully",
            "data": {
                'user_id' : response 
              }
            }
            return compress(response)  
        
  
