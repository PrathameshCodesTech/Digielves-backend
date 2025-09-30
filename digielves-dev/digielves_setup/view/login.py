  # Django Required Dependencies
# from gzip import compress
from django.shortcuts import render
from configuration.gzipCompression import compress
from digielves_setup.models import EmployeePersonalDetails, OrganizationDetails, OutsiderUser, User, UserCreation
from digielves_setup.send_emails.email_conf.send_otp import sendOTP
from digielves_setup.seriallizers.user import UserLoginSeriallizer
from rest_framework import viewsets
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page

from rest_framework import status

import requests
import logging

logger = logging.getLogger('api_hits')
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


class LogInClass(viewsets.ModelViewSet):

    # authentication_classes = [TokenAuthentication]
    print('i am here')
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle,UserRateThrottle]

    serializer_class = UserLoginSeriallizer
    print('sab par klardiya')

    # Client Registration API
    def logIn(self,request):
        # print(request.data)
        print('mai idher hu')
        try:
            with open('useful.csv') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    csv_key = row[0]

            csv_key = csv_key.replace('RUSH','')
            csv_key = csv_key.replace('ISHK','')
            # print(fernet)
            user_password = bcrypt.hashpw(request.data['password'].encode('utf-8')  , csv_key.encode('utf-8') )
            print('this si my pass',user_password)
            user = User.objects.get( email=request.data['email'].lower(), password= user_password )
            print(user,'this is user')
            try:
                User.objects.get( email=request.data['email'].lower(), password= user_password, active=True  )


            except Exception as e:
                response = {
                "success": False,
                "status": 123,
                "message": "Your account has been deactivated by the organization"
                }
                return JsonResponse(response)

            if user.user_role == "Dev::Employee":
                try:

                    user = User.objects.get(email=request.data['email'].lower(), password=user_password, employee_user_id__organization_id__user_id__active=True)


                except Exception as e:
                    response = {
                    "success": False,
                    "status": 123,
                    "error":str(e),
                    "message": "Your organization account has been deactivated"
                    }
                    return JsonResponse(response)


            token= RefreshToken.for_user(User.objects.get(id=user.id))
            print("Token Details")


            print(user.id)
            created_user_id = 0
            try:
                create_user = UserCreation.objects.get(employee_user_id = user.id )
                created_user_id = create_user.processed
            except Exception as e:
                pass

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

            if user.verified!="2":
                print("-----ahahahahaah")


                if user.user_role == "Dev::Employee" or user.user_role == "Dev::Doctor":
                    try:

                        print("employee_details-----employee_details")
                        print(user.id)

                        try:
                            employee_details = EmployeePersonalDetails.objects.get(user_id=user.id)
                        except Exception as e:


                            token_send = UserCreation.objects.get(employee_user_id=user.id)

                            response = {
                                "success": False,
                                "status": 202,
                                "user_id": user.id,
                                "email": user.email,
                                "temp_token":token_send.token,
                                'token': token_json,
                                "message": "Personal details Not Found",
                                "errors": str(e)
                                }
                            return JsonResponse(response)
                        print("-------hey")
                        print(employee_details)
                        print(employee_details.organization_id.id)
                        response = {
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "message": "Log-in successfully",
                        'token': token_json,
                        "data": {
                            'user_id' : user.id,
                            'user_role' : user.user_role,
                            'organization_id': employee_details.organization_id.id,
                            'name' : employee_details.firstname+" "+ employee_details.lastname,
                            'verified' : user.verified,
                            'processed' : created_user_id

                        },
                        "registration_token":  "create_user.token"

                        }
                        # response.set_cookie('jwt_token', token, httponly=True)

                        return compress(response)
                    except Exception as e:
                        print(e)
                        response = {
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "message": "Log-in successfully",
                        'token': token_json,
                        "data": {
                            'user_id' : user.id,
                            'user_role' : user.user_role,
                            'verified' : user.verified,
                            'name' : user.firstname+" "+ user.lastname,
                            'processed' : created_user_id

                        },
                        "registration_token":  "create_user.token"

                        }
                        # response.set_cookie('jwt_token', token, httponly=True)

                        return compress(response)



                elif user.user_role == "Dev::Admin":
                    response = {
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "message": "Log-in successfully",
                        'token': token_json,
                        "data": {
                            'user_id' : user.id,
                            'user_role' : user.user_role,

                            #'verified' : user.verified,
                            #'processed' : created_user_id

                        },
                        "registration_token":  "create_user.token"

                        }
                    return compress(response)


                elif user.user_role == "Dev::Outsider":
                    outsider = OutsiderUser.objects.get(related_id=user.id)
                    if outsider.processed=="1":
                        response = {
                            "success": False,
                            "status": 202,
                            "user_id": user.id,
                            "email": user.email,
                            "temp_token":token_send.token,
                            'token': token_json,
                            "message": "Personal details Not Found",
                            "errors": str(e)
                            }
                        return JsonResponse(response)
                    response = {
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "message": "Log-in successfully",
                        'token': token_json,
                        "data": {
                            'user_id' : user.id,
                            'user_role' : user.user_role,
                            'name' : user.firstname+" "+ user.lastname,
                            'verified' : user.verified,
                            # 'processed' : created_user_id

                        },
                        "registration_token":  "create_user.token"

                        }
                        # response.set_cookie('jwt_token', token, httponly=True)

                    return compress(response)

                else:
                    try:
                # Get the organization details associated with the user
                        organization_details = OrganizationDetails.objects.get(user_id=user.id)
                        organization_id = organization_details.id
                        response = {
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "message": "Log-in successfully",
                        'token': token_json,
                        "data": {
                            'user_id' : user.id,
                            'user_role' : user.user_role,
                            'verified' : user.verified,
                            'processed' : created_user_id,
                            'organization_id':user.id,
                            'name' : user.firstname+" "+ user.lastname,


                        },
                        "registration_token":  "create_user.token"

                        }
                        # response.set_cookie('jwt_token', token, httponly=True)

                        return compress(response)

                    except OrganizationDetails.DoesNotExist:
                        print("not exist")
                        pass
            else:
                response = {
           "success": True,
            "status": 403,
             "message": "Rejected User",
            }

            return compress(response)


        except Exception as e:
            response = {
            "success": False,
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Incorrect Login ID or Password",
                        "errors": str(e)
            }

            return compress(response)

    def createPassword(self,request):
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


            if user.user_role == "Dev::Outsider":
                response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Password changed successfully",
                "data": {
                    'user_id' : user.id,
                    'outsider': True
                }
                }
                return JsonResponse(response)
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

            token= RefreshToken.for_user(User.objects.get(id=user.id))

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


            if user.user_role == "Dev::Employee":
                employee_details = EmployeePersonalDetails.objects.get(user_id=user.id)

                response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Password changed successfully",
                'token': token_json,
                "data": {
                        'user_id' : user.id,
                        'user_role' : user.user_role,
                        'organization_id': employee_details.organization_id.id,
                        'name' : employee_details.firstname+" "+ employee_details.lastname,
                        'verified' : user.verified,


                            },
                }
            elif user.user_role == "Dev::Outsider":
                response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Password changed successfully",
                'token': token_json,
                "data": {
                        'user_id' : user.id,
                        'user_role' : user.user_role,
                        'name' : user.firstname+" "+ user.lastname,
                        'verified' : user.verified,


                            },
                }
            else:
                response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Password changed successfully",
                'token': token_json,
                "data": {
                        'user_id' : user.id,
                        'user_role' : user.user_role,
                        'name' : user.firstname+" "+ user.lastname,
                        'verified' : user.verified,


                            },
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
                sendOTP(request.data['email'], otp)
            else:
                email = request.data['email']

                sendOTP(request.data['email'], otp)

            cache.set(f'otp:{str(email)}', otp, timeout=800)
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


    def send_test_otp(self, request):
        try:
            mobile_number = request.data.get("mobile_number")
            otp = request.data.get("otp")
            client_ip = request.META.get('REMOTE_ADDR', 'unknown')
            logger.info(f"Received OTP request from IP: {client_ip}, Mobile Number: {mobile_number}")

            if mobile_number and otp:
                response = requests.get(f"https://digielvestech.in/messageOTP/sendOTP.php?mobile={mobile_number}&otp={otp}")

                if response.status_code == 200:
                    response_data = {
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "message": "OTP sent successfully",
                    }
                else:
                    response_data = {
                        "success": False,
                        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": "Failed to send OTP",
                        "errors": response.text
                    }
            else:
                response_data = {
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Mobile number or OTP not provided",
                }

            return JsonResponse(response_data)

        except requests.RequestException as e:
            response_data = {
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error in sending OTP",
                "errors": str(e)
            }
            return JsonResponse(response_data)
        except Exception as e:
            # Handle other exceptions
            response_data = {
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An unexpected error occurred",
                "errors": str(e)
            }
            return JsonResponse(response_data)

    def otpVerification(self,request):

        try:

            email = request.data['email']
            entered_otp = ''.join(request.data['otp'])
            print(entered_otp)
            print(email)
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
                sendOTP(request.data['email'], otp)
            else:
                user = User.objects.get( phone_no=request.data['email']  )
                sendOTP(request.data['email'], otp)



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
                created_user_id = 0
                try:
                    create_user = UserCreation.objects.get(user_id = user.id )
                    created_user_id = create_user.processed
                except:
                    pass

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


                if user.user_role == "Dev::Employee" or user.user_role == "Dev::Doctor":
                    try:

                        employee_details = EmployeePersonalDetails.objects.get(user_id=user.id)

                        response = {
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "message": "Log-in successfully",
                        'token': token_json,
                        "data": {
                            'user_id' : user.id,
                            'user_name': f'{user.firstname} {user.lastname}',
                            'user_role' : user.user_role,
                            'organization_id': employee_details.organization_id.id,
                            'verified' : user.verified,
                            'processed' : created_user_id

                        },
                        "registration_token":  "create_user.token"

                        }
                        # response.set_cookie('jwt_token', token, httponly=True)

                        return compress(response)
                    except Exception as e:
                        print(e)
                        response = {
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "message": "Log-in successfully",
                        'token': token_json,
                        "data": {
                            'user_id' : user.id,
                            'user_name': f'{user.firstname} {user.lastname}',
                            'user_role' : user.user_role,
                            'verified' : user.verified,
                            'processed' : created_user_id

                        },
                        "registration_token":  "create_user.token"

                        }
                        # response.set_cookie('jwt_token', token, httponly=True)

                        return compress(response)

                elif user.user_role == "Dev::Outsider":

                    response = {
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "message": "Log-in successfully",
                        'token': token_json,
                        "data": {
                            'user_id' : user.id,
                            'user_name': f'{user.firstname} {user.lastname}',
                            'user_role' : user.user_role,
                            'verified' : user.verified,

                        },
                        "registration_token":  "create_user.token"

                        }

                    return JsonResponse(response)
                else:
                    try:
                # Get the organization details associated with the user
                        organization_details = OrganizationDetails.objects.get(user_id=user.id)
                        organization_id = organization_details.id
                        response = {
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "message": "Log-in successfully",
                        'token': token_json,
                        "data": {
                            'user_id' : user.id,
                            'user_role' : user.user_role,
                            'verified' : user.verified,
                            'processed' : created_user_id,
                            'organization_id':organization_id

                        },
                        "registration_token":  "create_user.token"

                        }
                        # response.set_cookie('jwt_token', token, httponly=True)

                        return compress(response)

                    except OrganizationDetails.DoesNotExist:
                        print("not exist")
                        pass
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
        


