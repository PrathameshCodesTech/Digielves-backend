import csv
import datetime
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from configuration.authentication import JWTAuthenticationUser
from digielves_setup.models import SalesStatus, TaskStatus, User, UserCreation

# Authentication Modules for rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.permissions import  IsAuthenticated ,AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
from rest_framework.throttling import AnonRateThrottle,UserRateThrottle
from digielves_setup.seriallizers.user import UserRegistraionSerializer, UpdateUserRegistraionSerializer

from django.db.models import Max


from digielves_setup.models import OrganizationDetails, User, OrganizationBranch
from organization.seriallizers.organization_details_seriallizer import organizationDetailsSerializer, UpdateOrganizationDetailsSerializer

import bcrypt
from django.http import JsonResponse,HttpResponse
from rest_framework import status

import gzip
from django.views.decorators.gzip import gzip_page
from django.middleware.gzip import GZipMiddleware

from digielves_setup.validations import is_valid_password

from rest_framework.generics import GenericAPIView

# Create your views here.
class Registration(viewsets.ModelViewSet):

    #authentication_classes = [JWTAuthenticationUser]
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle,UserRateThrottle]

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
                    # create_user.processed = 1
                    # create_user.user_id = response.id
                    # create_user.save()
                    
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
                        "message": "Failed to register u ser",
                        "errors": str(user.error)
                        })   
                
                
        except Exception as e:
            return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to register user",
                        "errors": str(e)
                        })



    #Client Registration API 
    @csrf_exempt
    def UserRegistraion(self, request):
        
        print(request.data)
        user_object = User()
    
        with open('useful.csv') as f:
            reader = csv.reader(f)
            next(reader)  # <- skip the header row
            for row in reader:
                csv_key = row[0]
    
        csv_key = csv_key.replace('RUSH', '')
        csv_key = csv_key.replace('ISHK', '')
    
        try:
            
            print(request.data['password'])
            user_object.password = bcrypt.hashpw(request.data['password'].encode('utf-8'), csv_key.encode('utf-8'))
            
            user = UserRegistraionSerializer(user_object, data=request.data)
            
    
            if user.is_valid():
                
                try:
                    response = user.save()
                    
    
                    organizationDetails = OrganizationDetails()
    
                    
                    print(user_object.id)
    
                    user_instance = User.objects.get(id=user_object.id)
    
                    organizationDetails.user_id = user_instance
    
                    user = User.objects.get(id=user_object.id, user_role="Dev::Organization")
    
                    try:
                        userAddressSerialData = organizationDetailsSerializer(organizationDetails, data=request.data)
    
                        if userAddressSerialData.is_valid(raise_exception=True):
                        
                            try:
                                userAddressSerialData.save()
    
                                user.verified = 1
                                user.save()
    
                                branch_name = request.data['branch_name']
                                address = request.data['address']
    
                                organization_details_instance = OrganizationDetails.objects.get(id=organizationDetails.id)
    
                                organization_branch = OrganizationBranch(
                                    org=organization_details_instance, branch_name=branch_name, Address=address)
                                organization_branch.save()
                                
                                
                                try:
                                    # Create default task statuses
                                    for status_data in [
                                        {"status_name": "Pending", "fixed_state": "Pending", "color": "#fb9e00", "order": 1},
                                        {"status_name": "Completed", "fixed_state": "Completed", "color": "#009ce0", "order": 2},
                                        {"status_name": "Closed", "fixed_state": "Closed", "color": "#33cc33", "order": 3}
                                    ]:
                                        TaskStatus.objects.create(organization=organizationDetails, **status_data)
                                    # Create default sales statuses
                                    for sales_status_data in [
                                        {"status_name": "Unmapped", "fixed_state": "Unmapped", "color": "#e27300", "order": 1},
                                        {"status_name": "Assigned", "fixed_state": "Assigned", "color": "#68bc00", "order": 2},
                                        {"status_name": "Contacted", "fixed_state": "Contacted", "color": "#16a5a5", "order": 3},
                                        {"status_name": "In Progress", "fixed_state": "InProgress", "color": "#7b64ff", "order": 4},
                                        {"status_name": "Qualified", "fixed_state": "Qualified", "color": "#b0bc00", "order": 5},
                                        {"status_name": "Lost", "fixed_state": "Lost", "color": "#c45100", "order": 6},
                                        {"status_name": "Pending Approval", "fixed_state": "PendingApproval", "color": "#a4dd00", "order": 7},
                                        {"status_name": "Won", "fixed_state": "Won", "color": "#68bc00", "order": 8}
                                    ]:
                                        SalesStatus.objects.create(organization=organizationDetails, **sales_status_data)
                                except Exception as e:
                                    user_instance.delete()
                                    return JsonResponse({
                                        "success": False,
                                        "status": status.HTTP_400_BAD_REQUEST,
                                        "message": "Failed to create status",
                                        "errors": str(e)
                                    })
    
                                return JsonResponse({
                                    "success": True,
                                    "status": status.HTTP_201_CREATED,
                                    "message": "User created successfully",
                                    "data": {
                                        "organization_id": organizationDetails.id
                                    }
                                })
    
                            except Exception as e:
                                # Handle exceptions related to adding organization details
                                user_instance.delete()
                                return JsonResponse({
                                    "success": False,
                                    "status": status.HTTP_400_BAD_REQUEST,
                                    "message": "Failed to add details",
                                    "errors": str(e)
                                })
    
                    except Exception as e:
                        user_instance.delete()
                        return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Failed to add organization details",
                            "errors": str(e)
                        })
    
    
                except Exception as e:
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
                    "email_error":True,
                    "message": "email already exist",
                    "errors": str(user.errors) 
                })

    
        except Exception as e:
        
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to register user",
                "errors": str(e)
            })



