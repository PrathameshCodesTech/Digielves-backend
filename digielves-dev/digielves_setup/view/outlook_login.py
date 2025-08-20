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
from json import dumps

from django.http import HttpResponseRedirect



def OutlooklogIn(request):
    # Get parameters from the request
    from_local = request.GET.get('from_local')
    redirect_to = request.GET.get('redirect_to')

    # Set base redirect_uri
    if from_local == 'true':
        base_redirect_uri = "http://localhost:3000"
    else:
        base_redirect_uri = "https://vibecopilot.ai"

    # Append the appropriate path to the base URI
    if redirect_to == 'calender':
        redirect_uri = f"{base_redirect_uri}/employee/calender"
    else:
        redirect_uri = f"{base_redirect_uri}/employee/settings"

    # Construct the final URL
    client_id = "33d46bb8-945b-4c07-bf6c-74f89c263b23"
    tenant_id = "ad2b1ce8-b182-443b-bc9c-1db30df9f99e"
    scope = "offline_access%20User.Read%20Mail.Read"
    state = "12345"

    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&response_mode=query&scope={scope}&state={state}"

    # Redirect the user to the constructed URL
    response = HttpResponseRedirect(url)
    return response
# def OutlooklogIn(request):
#     url = "https://login.microsoftonline.com/ad2b1ce8-b182-443b-bc9c-1db30df9f99e/oauth2/v2.0/authorize?client_id=33d46bb8-945b-4c07-bf6c-74f89c263b23&response_type=code&redirect_uri=https://vibecopilot.ai/employee/settings&response_mode=query&scope=offline_access%20User.Read%20Mail.Read&state=12345"
#     response_out = requests.get(url)
#     print(response_out.ok )
        


#     response = HttpResponseRedirect(url)
#     print("🚀 ~ response:", response)
    

#     # Return the HTTP response object from the view.
#     return response



#     content = response_out.text 
#     print(content[0:1000])

#     response = HttpResponse(content_type='text/html')

#     response.content = response_out.text

#     # Return the HTTP response object from the view.
#     return response




class OutlookLogInClass(viewsets.ModelViewSet):
      
     # authentication_classes = [TokenAuthentication]

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle,UserRateThrottle]


    def get_outlookTokens(self, request):
        print("--------------------------hey")
        code = request.GET.get('code') 
        print(code )
        redirect_uri = request.GET.get('redirect_uri') 
        print("--------------------------hey")
        print(redirect_uri)



        url = "https://login.microsoftonline.com/ad2b1ce8-b182-443b-bc9c-1db30df9f99e/oauth2/v2.0/token"

        payload = f'client_id=33d46bb8-945b-4c07-bf6c-74f89c263b23&scope=User.Read%20Mail.Read&code={code}&redirect_uri%20={redirect_uri}&grant_type=authorization_code&client_secret=jQd8Q~_GsRrLZoBULCcHe5Rx1wxpzDivMdNWQc0J'
        # VALID TILL 2 JAN 2026 (client_secret)
        headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Bearer {code}',
        'Cookie': 'buid=0.AT0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA.AQABAAEAAAAtyolDObpQQ5VtlI4uGjEPi-aPm_4BVCbTIwx6dd_ZBStD0gnfOtojp6dfeCZIsuqpyXXPafM4y6LUNr6v0T4KkFENfRkVCmvRGjqDiF-uirRhMf8u7Mqd9d2fFgkPrJIgAA; fpc=AsSTY0zUYGZPkoyRtX1bNPDT1neRAQAAAKRN1NwOAAAA; stsservicecookie=estsfd; x-ms-gateway-slice=estsfd'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print(response.text)

        return JsonResponse({'data': response.json()}, status=response.status_code)

        





     
        
  
