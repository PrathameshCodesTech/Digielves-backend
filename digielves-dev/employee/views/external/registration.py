# views.py
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from configuration.userCreationToken import generate_random_string
from digielves_setup.models import EmployeePersonalDetails, OrganizationBranch, OrganizationDetails, User, UserCreation
from employee.seriallizers.external.registration import EmployeeRegSerializer, ExtOrganizationBranchSerializer, ExtOrganizationDetailsSerializer, OrgUserSerializer, UserCreationRegSerializer, UserRegUserSerializer
from rest_framework.permissions import  AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
import bcrypt
import csv
from configuration.gzipCompression import compress
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
import datetime
from django.db import transaction

class UserWithOrganizationDetailsView(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    

    throttle_classes = [AnonRateThrottle,UserRateThrottle]
    @csrf_exempt
    def create_organization(self, request):
        try:
            # Load and process the CSV key
            with open('useful.csv') as f:
                reader = csv.reader(f)
                next(reader)  # Skip the header row
                for row in reader:
                    csv_key = row[0]
                    
            csv_key = csv_key.replace('RUSH', '').replace('ISHK', '')
            # Copy and modify request data for User creation
            request_data = request.data.copy()
            organization_name = request_data.get('organization_name')
            if not organization_name or len(organization_name) < 3:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid organization name. It must be at least 3 characters long."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            branch_name = request_data.get('branch_name')
            if not branch_name or len(branch_name) < 3:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid branch name. It must be at least 3 characters long."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            request_data['user_role'] = 'Dev::Organization'
            request_data['user_type'] = 'Normal'
            request_data['verified'] = 1
            request_data['firstname'] = request_data['organization_name'].split(" ")[0]
            request_data['lastname'] = " ".join(request_data['organization_name'].split(" ")[1:])
            request_data['active'] = True
            
            # Hash the password with the csv_key
            request_data['password'] = bcrypt.hashpw(
                request.data['password'].encode('utf-8'), 
                csv_key.encode('utf-8')
            ).decode('utf-8')
            
            with transaction.atomic():    
                # User creation
                user_serializer = OrgUserSerializer(data=request_data)
                if not user_serializer.is_valid():
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid user data",
                        "errors": user_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                user = user_serializer.save()
                # OrganizationDetails creation
                
                
                organization_data = {
                    'user_id': user.id,
                    'name': request.data.get('organization_name'),
                    'support_mail': request.data.get('support_mail'),
                    'number_of_employee': request.data.get('number_of_employee', 0),
                    'number_of_subscription': request.data.get('number_of_subscription', 0),
                    'mail_extension': request.data.get('mail_extension'),
                    'organization_code': request.data.get('organization_code'),
                    'org_description': request.data.get('org_description'),
                    'org_website_link': request.data.get('org_website_link'),
                }
                org_serializer = ExtOrganizationDetailsSerializer(data=organization_data)
                if not org_serializer.is_valid():
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid organization data",
                        "errors": org_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                organization = org_serializer.save()
                
                # OrganizationBranch creation
                branch_data = {
                    'org': organization.id,
                    'branch_name': request.data.get('branch_name'),
                    'Address': request.data.get('branch_address')
                }
                branch_serializer = ExtOrganizationBranchSerializer(data=branch_data)
                if not branch_serializer.is_valid():
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid branch data",
                        "errors": branch_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                branch_serializer.save()
                
                # Return success response
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Organization and branch created successfully",
                    "user_data": user_serializer.data,
                    "organization_data": org_serializer.data,
                    "branch_data": branch_serializer.data
                }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred during creation",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserRegDetailsView(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    

    throttle_classes = [AnonRateThrottle,UserRateThrottle]

    @csrf_exempt
    def register_employee(self, request):
        try:
            # Copy and modify request data for User creation
            request_data = request.data.copy()
            request_data['user_role'] = 'Dev::Employee'
            request_data['user_type'] = 'Normal'
            request_data['verified'] = 1
            request_data['active'] = True
            request_data['firstname'] = request_data['name'].split(" ")[0]
            request_data['lastname'] = " ".join(request_data['name'].split(" ")[1:])
            
            with open('useful.csv') as f:
                reader = csv.reader(f)
                next(reader)  # Skip the header row
                for row in reader:
                    csv_key = row[0]
                    
            csv_key = csv_key.replace('RUSH', '').replace('ISHK', '')
            # Hash the password
            password = request_data.get('password')
            request_data['password'] = bcrypt.hashpw(password.encode('utf-8'), csv_key.encode('utf-8')).decode('utf-8')

            with transaction.atomic():  
                # User creation
                user_serializer = UserRegUserSerializer(data=request_data)
                if not user_serializer.is_valid():
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid user data",
                        "errors": user_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                user = user_serializer.save()

                org_instance = OrganizationDetails.objects.get(id = request_data.get('organization_id'))
                org_branch_instance = OrganizationBranch.objects.filter(org = request_data.get('organization_id')).first()
                # EmployeePersonalDetails creation
                employee_data = {
                    'user_id': user.id,
                    'organization_id': request_data.get('organization_id'),
                    'organization_location':  request_data.get('organization_location',org_branch_instance ),
                    'employee_id': request_data.get('company_employee_id'),
                    'firstname': request_data['name'].split(" ")[0],
                    'lastname': " ".join(request_data['name'].split(" ")[1:]),
                    'date_of_birth': request_data.get('date_of_birth'),
                    'phone_no': request_data.get('phone_no'),
                    'job_title': request_data.get('job_title'),
                    'designation': request_data.get('designation'),
                    'department': request_data.get('department'),
                    'gender': request_data.get('gender'),
                    'work_location': request_data.get('work_location'),
                    'profile_picture': request_data.get('profile_picture')
                }
                emp_serializer = EmployeeRegSerializer(data=employee_data)
                if not emp_serializer.is_valid():
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid employee data",
                        "errors": emp_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                emp_serializer.save()
                token = generate_random_string(52)
                # UserCreation creation
                user_creation_data = {
                    'organization_id': org_instance.id,
                    'organization_location': request_data.get('organization_location', org_branch_instance),
                    'created_by': org_instance.id,  # Assuming the request is authenticated
                    'employee_user_id': user.id,
                    'email': user.email,
                    'company_employee_id': request_data.get('company_employee_id'),
                    'token': token,
                    'processed': 3,
                    'verified': 1,
                }
                user_creation_serializer = UserCreationRegSerializer(data=user_creation_data)
                if not user_creation_serializer.is_valid():
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid user creation data",
                        "errors": user_creation_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                user_creation_serializer.save()

                # Return success response
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Employee created successfully",
                    "user_data": user_serializer.data,
                    "employee_data": emp_serializer.data,
                    "user_creation_data": user_creation_serializer.data
                }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred during employee registration",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    
    def ExternalUserlogIn(self,request):
        try:
            with open('useful.csv') as f:
                reader = csv.reader(f)
                next(reader)      
                for row in reader:
                    csv_key = row[0]

            csv_key = csv_key.replace('RUSH','')
            csv_key = csv_key.replace('ISHK','')
            # print(fernet)
            
            user = User.objects.get( external_user_id=request.data['external_user_id'])
            
            try:
                User.objects.get( external_user_id=request.data['external_user_id'], active=True  )
                
                
            except Exception as e:
                response = {
                "success": False,
                "status": 123,                
                "message": "Your account has been deactivated by the organization"
                }
                return JsonResponse(response)

            if user.user_role == "Dev::Employee":
                try:

                    user = User.objects.get(external_user_id=request.data['external_user_id'], employee_user_id__organization_id__user_id__active=True)

                    
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
            
            
                if user.user_role == "Dev::Employee" or user.user_role == "Dev::Doctor":
                    try:
                        
                  
                        
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
    
