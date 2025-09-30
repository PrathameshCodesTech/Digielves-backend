from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from datetime import datetime, timedelta
import jwt
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken

from digielves_setup.models import User

from rest_framework.permissions import BasePermission


def authenticateUser(auth_header,request_user_id ):
    print("--------------hii")
    if not auth_header.startswith('Bearer'):
        raise exceptions.AuthenticationFailed('Invalid authentication header')

    token = auth_header.split(' ')[1].strip()
    try:
        decoded_token = AccessToken(str(token)).payload

        print(decoded_token)
        user_id = decoded_token.get('user_id')
        print(user_id)
        if str(user_id) == str(request_user_id) :
            user = User.objects.get(id=user_id)
            return user, decoded_token
    except jwt.DecodeError:
        raise exceptions.AuthenticationFailed('Invalid token signature')
    except jwt.ExpiredSignatureError:
        raise exceptions.AuthenticationFailed('Token expired')
    
    raise exceptions.AuthenticationFailed('Invalid token')


class JWTAuthenticationUser(JWTAuthentication):

    
    def authenticate(self,request):
        print("Hiiiiii")
        auth_header = request.headers.get('Authorization', '')
        print(auth_header)
        try:
            request_user_id = request.GET.get('user_id')
        except:
            pass
        
        try:
            request_user_id = request.data['user_id']
        except:
            pass
        return authenticateUser(auth_header,request_user_id )




class JWTAuthenticationAdmin(JWTAuthentication):

    
    def authenticate(self,request):
        print("Hiiiiii")
        auth_header = request.headers.get('Authorization', '')
        print(auth_header)
        try:
            request_user_id = request.GET.get('user_id')
        except:
            pass
        
        try:
            request_user_id = request.data['user_id']
        except:
            pass
        
    
        if not auth_header.startswith('Bearer'):
            raise exceptions.AuthenticationFailed('Invalid authentication header')

        token = auth_header.split(' ')[1].strip()
        try:
            decoded_token = AccessToken(str(token)).payload

            print(decoded_token)
            user_id = decoded_token.get('user_id')
            print(user_id)
            if str(user_id) == str(request_user_id) :
                user = User.objects.get(id=user_id, user_role= "Dev::Admin")
                
                
                
                return user, decoded_token
        except jwt.DecodeError:
            raise exceptions.AuthenticationFailed('Invalid token signature')
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token expired')
        
        raise exceptions.AuthenticationFailed('Invalid token')




    




