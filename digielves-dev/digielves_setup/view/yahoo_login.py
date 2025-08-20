from django.shortcuts import render

# Create your views here.
# yahoologin/views.py
import requests     
from django.http import JsonResponse


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
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


# Authentication Modules for rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.permissions import  IsAuthenticated ,AllowAny

from django.db.models import Max
from django.shortcuts import redirect
import requests
from django.http import HttpResponse
#from django.shortcuts import redirect
from django.views import View
from urllib.parse import urlencode
import base64
from django.shortcuts import redirect
from requests import post, get
import re   


# Application Response Serializer 


class YahooLogInClass(viewsets.ModelViewSet):
      
     # authentication_classes = [TokenAuthentication]

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle,UserRateThrottle]
    
    
    
    client_id = 'dj0yJmk9QWhjUHRHNk03bzRFJmQ9WVdrOWIwczFRalpoVkVvbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PTli'
    client_secret = 'ab1c9fcf4fee77330e47312797149fb299b885db'
    base_url = 'https://api.login.yahoo.com/'  
    redirect_uri = 'https://ordinet.store/api/yahoo-login/'  


    def send_to_login(self, request):
        lang = re.split('[,;/ ]+', request.headers.get('Accept-Language'))[0]
        code_url = f'oauth2/request_auth?client_id={self.client_id}&redirect_uri={self.redirect_uri}&response_type=code&scope=openid&language={lang}'
        url = self.base_url + code_url
        print(url)  # Add this line for debugging 
        return redirect(url, )

    def get_tokens(self, request):
        code = request.GET.get('code') 
        encoded = base64.b64encode((self.client_id + ':' + self.client_secret).encode('utf-8'))
        headers = {
            'Authorization': f'Basic {encoded.decode("utf-8")}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
            'code': code
        } 
        response = post(self.base_url + 'oauth2/get_token', headers=headers, data=data)
        
        if response.ok:
            return JsonResponse(response.json())  # or use HttpResponse instead of JsonResponse if needed
        else:
            # Handle the error case appropriately, e.g., return an error response
            return JsonResponse({'error': 'Failed to get tokens'}, status=response.status_code)

    

    def get_user_info(self, request):       
        access_token = request.GET.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        response = get(self.base_url + 'openid/v1/userinfo', headers=headers)
        if response.ok:
            return JsonResponse(response.json())  # or use HttpResponse instead of JsonResponse if needed
        else:
            # Handle the error case appropriately, e.g., return an error response
            return JsonResponse({'error': 'Failed to get tokens'}, status=response.status_code)



  































     

  #  def yahoo_callback(self, request):

        # Step 3: Exchange the authorization code for an access token

   #     token_url = 'https://api.login.yahoo.com/oauth2/get_token'
    #    client_id = 'dj0yJmk9QWhjUHRHNk03bzRFJmQ9WVdrOWIwczFRalpoVkVvbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PTli'
     #   client_secret = 'ab1c9fcf4fee77330e47312797149fb299b885db'
      #  redirect_uri = 'https://ordinet.store/api/yahoo-login/'
       # authorization_code = request.GET.get('code')
    
        # Exchange the authorization code for an access token
        #data = {
         #   'grant_type': 'authorization_code',
          #  'redirect_uri': redirect_uri,
           # 'code': authorization_code,
            #'client_id': client_id,
           # 'client_secret': client_secret,
        #}
        #response = requests.post(token_url, data=data)
    
        # Print the response
        #print(response.json())
    
        # Handle the response and return an appropriate response to the user
        #return HttpResponse('Logged in with Yahoo!')

    

###############################################################################################################################
   # def yahoo_login(self,request): 
        
    #    client_id = 'dj0yJmk9QWhjUHRHNk03bzRFJmQ9WVdrOWIwczFRalpoVkVvbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PTli'
     #   redirect_uri = 'https://ordinet.store/yahoo.html'
      #  auth_endpoint = 'https://api.login.yahoo.com/oauth2/request_auth'

       # params = {
        #    'client_id': client_id,
         #   'redirect_uri': redirect_uri,
          #  'response_type': 'code',
           # 'scope': 'openid mail-r',
            #'nonce': 'YOUR_NONCE',
          #}

        #auth_url = f'{auth_endpoint}?{"&".join([f"{k}={v}" for k, v in params.items()])}'

        #return redirect(auth_url)

    #def yahoo_callback(request):

     #   client_id = 'dj0yJmk9QWhjUHRHNk03bzRFJmQ9WVdrOWIwczFRalpoVkVvbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PTli'
      #  client_secret = 'ab1c9fcf4fee77330e47312797149fb299b885db'
       # redirect_uri = 'https://ordinet.store/yahoo.html'
        #token_endpoint = 'https://api.login.yahoo.com/oauth2/get_token'

        #code = request.GET.get('code')

        #data = {
         #  'client_id': client_id,
          #  'client_secret': client_secret,
           # 'redirect_uri': redirect_uri,
            #'code': code,
            #'grant_type': 'authorization_code',
         #}

        #response = requests.post(token_endpoint, data=data)
       # response_data = response.json()

        #access_token = response_data['access_token']
        #refresh_token = response_data['refresh_token']
                       
        # Process the tokens and perform further actions as needed

        #return redirect('YOUR_REDIRECT_URL')

############???????????????????????????????////////

     #   client_id = 'dj0yJmk9ZWlpaFB2TWNNZGJXJmQ9WVdrOVpXMXFjRzFZTVVFbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PTc4'
      #  client_secret = 'e039b733257e0887c8c403e3b51844f9a2c87d45'
       # base_url = 'https://api.login.yahoo.com/'
     #   redirect_uri = "https://127.0.0.1:5000/dashboard"

    #def send_to_login(request):
     #   lang = re.split('[,;/ ]+', request.accept_languages.to_header())[0]
      #  code_url = f'oauth2/request_auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=openid&language={lang}'
       # url = base_url + code_url
        #return redirect(url, code=302)

    #def get_tokens(request):
     #   code = request.args.get('code')
      #  encoded = base64.b64encode((client_id + ':' + client_secret).encode("utf-8"))
       # headers = {
        #    'Authorization': f'Basic {encoded.decode("utf-8")}',
         #   'Content-Type': 'application/x-www-form-urlencoded'
        #}
        #data = {
         #   'grant_type': 'authorization_code',
          #  'redirect_uri': redirect_uri,
           # 'code': code
        #}
        #response = post(base_url + 'oauth2/get_token', headers=headers, data=data)
        #response.ok
        #return response.json()

    #def get_user_info(request):
     #   access_token = response.json()['Access_token']
      #  headers = {
       #     'Authorization': f'Bearer {access_token}',
        #    'Accept': 'application/json',
         #   'Content-Type': 'application/json'
        #}
        #response = get(base_url + 'openid/v1/userinfo', headers=headers)
        #response.ok
        #return response.json()





#######################################################################################################3

        # Authorization code received from JavaScript  

        # authorization_code = request.GET.get('code')
                                                        
        # Yahoo API credentials

        #client_id='dj0yJmk9QWhjUHRHNk03bzRFJmQ9WVdrOWIwczFRalpoVkVvbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PTli'   
        #client_secret = 'ab1c9fcf4fee77330e47312797149fb299b885db'

        # Redirect URI for Yahoo to redirect after authorization

        #redirect_uri = 'https://ordinet.store/yahoo.html'

        # Exchange authorization code for access token

        #token_url = 'https://api.login.yahoo.com/oauth2/get_token'
        #data = {
         #   'client_id': client_id,
          #  'client_secret': client_secret,
          #  'redirect_uri': redirect_uri, 
           # 'code': authorization_code,
            #'grant_type': 'authorization_code'
        #}
        #response = requests.post(token_url, data=data)

        # Process the response and extract access token

        #if response.status_code == 200:
         #   data = response.json()
          #  access_token = data['access_token']
           # expires_in = data['expires_in']
            #refresh_token = data['refresh_token']
            # Make API calls to retrieve user information using the access token
            # ...
            #return JsonResponse({'success': True, 'message': 'Login successful'})
        #else:
         #   return JsonResponse({'success': False, 'message': 'Login failed'})




