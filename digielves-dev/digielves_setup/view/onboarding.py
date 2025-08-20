import base64
import json
import random
from django.shortcuts import render
from configuration.authentication import JWTAuthenticationUser
from configuration.onboardingEmail import sendMail
from configuration.userCreationToken import generate_random_string
from digielves_setup.models import OutsiderUser, PersonalStatus, ReportingRelationship, UserCreation, User, OrganizationDetails, EmployeePersonalDetails, OrganizationBranch, OrganizationDetails
from digielves_setup.send_emails.email_conf.send_onboard_link import sendOnBoardLink
from digielves_setup.seriallizers.user_creation_seriallizer import GetHierarchySSerializers, InviteUserCreationSerializers,CreatingUserCreationSerializers, OutsiderUserSerializers, SendEmailserializers, UserCreationApprovedSerializers, UserCreationSerializers,UpdateUserCreationSerializers,UserCreationSerializersForUsers

from rest_framework import viewsets
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status

from django.core.serializers import serialize

# Authentication Modules for rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.permissions import  IsAuthenticated ,AllowAny

from django.db.models import Max
import threading

from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
# Application Response Serializer 

from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
import pandas as pd
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.db import transaction

from django.db.models import Subquery, OuterRef
class UserCreationClass(viewsets.ModelViewSet):

    # authentication_classes = [JWTAuthenticationUser]
    # permission_classes = [IsAuthenticated]
    # # permission_classes = [AllowAny]

    # throttle_classes = [AnonRateThrottle,UserRateThrottle]
    serializer_class= UpdateUserCreationSerializers
    

    @csrf_exempt
    def createUser(self, request):
        try:
            print("----------dard")
            print(request.data)
            # Check if the user with the given email already exists
            existing_user = UserCreation.objects.filter(email=request.data['email']).first()
            if existing_user:
                return JsonResponse({
                    "success": False,
                    "status": 122,
                    "message": "It seems that username is already in use. Please choose a different username to continue. ",
                })
    
            
            user_data = request.data.copy()
            del user_data['organization_id']
            
            serializer = CreatingUserCreationSerializers(data=user_data)
            if serializer.is_valid():

                org_user_id = request.data['organization_id']
                
                
                
                
                
                try:
                    # for employee
                    org = get_object_or_404(OrganizationDetails, id=org_user_id)
                    print("----------hmmm")
                    serializer.validated_data['organization_id'] = org
                    print(org.number_of_employee)
                    if org.number_of_employee:
                        print("-----------------------ha")
                        if org.number_of_employee>=org.number_of_subscription:
                            return JsonResponse({
                                    "success": False,
                                    "status": 123,
                                    "message": "Sorry, you've reached the limit of your subscription plan for the number of employees. Please consider upgrading your subscription to accommodate more users.",
                                
                                })
                    else:
                        pass
                         
                    
                    
                    user_instance=User.objects.get(id=request.data['user_id'])
                    employee_instance=EmployeePersonalDetails.objects.get(user_id=user_instance)
                    
                    token = generate_random_string(52)
                    serializer.validated_data['token'] = token
                    
                    serializer.validated_data['organization_location'] = employee_instance.organization_location
                    
                    new_user = serializer.save()
                    
                    org.number_of_employee+=1
                    org.save()
        
                    
                    
                    t = threading.Thread(target=thread_to_send_invitation, args=(user_data['email'],str(token)))
                    t.setDaemon(True) 
                    t.start() 
                    
                    
                except (EmployeePersonalDetails.DoesNotExist, Http404):
                    # for Organization
                    
                    org = get_object_or_404(OrganizationDetails, user_id=org_user_id)
                    if org.number_of_employee:
                        if org.number_of_employee>=org.number_of_subscription:
                            return JsonResponse({
                                    "success": False,
                                    "status": 123,
                                    "message": "Sorry, you've reached the limit of your subscription plan for the number of employees. Please consider upgrading your subscription to accommodate more users.",
                                
                                })
                    else:
                        pass
                    
                    
                    serializer.validated_data['organization_id'] = org
                    
                    
                    token = generate_random_string(52)
                    serializer.validated_data['token'] = token
                    
                    
                    new_user = serializer.save()
                    
                    org.number_of_employee+=1
                    
                    org.save()

                    t = threading.Thread(target=thread_to_send_invitation, args=(user_data['email'],str(token)))
                    t.setDaemon(True) 
                    t.start() 
    
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "User Created Successfully",
                    "data": {
                        "user_creation_id": new_user.id
                    }
                })
    
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to Create User",
                "errors": serializer.errors
            })
    
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error.",
                "errors": str(e)
            })



                         
    @csrf_exempt
    def bulkCreateUser(self,request):
        uploaded_file = request.FILES.get('excel_file')

        if not uploaded_file:
            return JsonResponse({'error': 'No file was uploaded.'}, status=400)

        if not uploaded_file.name.endswith('.xlsx'):
            return JsonResponse({'error': 'Only Excel files (xlsx) are supported.'}, status=400)

        df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        expected_columns = ['Report to Email', 'Email', 'Employee id', 'Reporting Hierarchy']
        actual_columns = df.columns.tolist()

        if not set(expected_columns).issubset(set(actual_columns)):
            return JsonResponse({
                "success": False,
                "status": 124, 
                "message": f"Expected columns {', '.join(expected_columns)}, but found {', '.join(actual_columns)}",
            })

        
        # Check if all emails are valid
        
        invalid_emails = df.loc[~df['Email'].apply(lambda x: pd.notna(x) and '@' in str(x) and '.' in str(x)), 'Email']
        if not invalid_emails.empty :
            return JsonResponse({
                "success": False,
                "status": 124,
                "message": f"Invalid Email found in the email column: {', '.join(invalid_emails)}",
            })
        df.drop_duplicates(subset=['Report to Email', 'Email'], keep='first', inplace=True)
        print(df)
        if df.duplicated(subset=['Report to Email', 'Email']).any():
            return JsonResponse({
                "success": False,
                "status": 124, 
                "message": "Duplicate values found in 'Report to Email' and 'Email' columns.",
            })


        # Check if employee_id column contains unique values
        df.drop_duplicates(subset=['Employee id', 'Report to Email', 'Email'], keep='first', inplace=True)
        if df.duplicated(subset=['Report to Email', 'Email','Employee id']).any():
            return JsonResponse({
                "success": False,
                "status": 124, 
                "message": "Duplicate values found in 'Report to Email' and 'Email' columns.",
            })
        
        
        # Check for duplicate 'Employee id' values
        duplicate_employee_ids = df[df.duplicated(subset=['Employee id'], keep=False)]['Employee id']

        # Check if 'Employee id' values have different 'Email' values
        email_check = df[df['Employee id'].isin(duplicate_employee_ids)][['Employee id', 'Email']]

        # Filter rows where 'Employee id' has different 'Email'
        different_email_check = email_check.groupby('Employee id')['Email'].nunique()

        if different_email_check.gt(1).any():
            # Duplicate 'Employee id' with different 'Email' values found   
            duplicate_employee_ids_with_different_email = different_email_check[different_email_check.gt(1)].index
            return JsonResponse({
                "success": False,
                "status": 124,
                "message": f"Duplicate Employee id found in the Employee id column: {', '.join(map(str, duplicate_employee_ids_with_different_email))} with different 'Email' values.",
            })

            

        error_email =[]
        existing_emails = []
        for index, row in df.iterrows():
            # print(row[0])
            email = row['Email'].lower() if not pd.isna(row['Email']) else None

            hierarchy_value=row['Reporting Hierarchy']

            reporting_to_email = row['Report to Email'].lower() if not pd.isna(row['Report to Email']) else None
            company_employee_id = row['Employee id']

            if not pd.isna(email):
                try:
                    
                    creation_id = UserCreation.objects.get(email=email)
               
                    try:
                        if not pd.isna(hierarchy_value):
                            hierarchy_key = int(hierarchy_value)
                            try:
                                user_creation_id = UserCreation.objects.get(email=reporting_to_email)

                                
                                
                                reporting_to_user = UserCreation.objects.get(email=reporting_to_email)
                                creation_id.reporting_to.add(reporting_to_user, through_defaults={'hierarchy': hierarchy_key})
                                creation_id.save()
                            except Exception as e:
                                return JsonResponse({
                                "success": False,
                                "status": status.HTTP_400_BAD_REQUEST, 
                                "message": "Failed to User",
                                "errors": str(e)
                                })
                                # error_email.append(reporting_to_email)
                            
                        else:
                            pass
                    except Exception as e:
                        return JsonResponse({
                                "success": False,
                                "status": status.HTTP_400_BAD_REQUEST, 
                                "message": "Failed to Create User",
                                "errors": str(e)
                                })
                except ObjectDoesNotExist:
                 
                    userDetails = UserCreation()
                 
                    org_details=OrganizationDetails.objects.get(user_id = request.data['organization_id'])
                    token = generate_random_string(52)
                    userDetails.token = token
                    userDetails.email = email
                    userDetails.organization_location=OrganizationBranch.objects.get(id = request.data['organization_location'])
                    userDetails.organization_id = org_details
                    userDetails.created_by = User.objects.get(id=request.data['created_by'])
                    
                    
                    userDetails.company_employee_id = company_employee_id

                    
                    try:
    
                        user_creation_id = UserCreation.objects.get(email=reporting_to_email)
                  
                        if not pd.isna(hierarchy_value):
                            hierarchy_key = int(hierarchy_value)
                            userDetails.save()
                            userDetails.reporting_to.add(user_creation_id, through_defaults={'hierarchy': hierarchy_key})
                        else:
                            userDetails.save()
                            userDetails.reporting_to.add(user_creation_id, through_defaults={'hierarchy': 1})
                    except Exception as e:
                 
                        # userDetails.reporting_hierarchy=None
                        pass
                        
                    #print(token)
                    if org_details.number_of_employee:
                    
                        if org_details.number_of_employee>=org_details.number_of_subscription:
                            return JsonResponse({
                                    "success": False,
                                    "status": 123,
                                    "message": "Subscription limit reached. Upgrade for more users; some employees may not be created.",                               
                                })
                    else:
                        pass
                    

                    org_details.number_of_employee+=1
                    org_details.save()
                    
                    
                    # sendOnBoardLink(email, "https://vibecopilot.ai/?access="+ str(token))
                    t = threading.Thread(target=thread_to_send_invitation, args=(email, str(token)))

                    t.setDaemon(True) 
                    t.start() 
                    
                    userDetails.save()
        
                    
            else:
                pass
        #print(existing_emails)
        # existing_emails_str = ", ".join(existing_emails) if existing_emails else "Nothing"

        return JsonResponse({
        "success": True,
        "status": status.HTTP_201_CREATED, 
        "sub_status" :100 if error_email else 201 ,            
        "message": "Users Created successfully",
        "data":""
           
        })
        
    
    @csrf_exempt
    def bulkCancelUser(self,request):

        uploaded_file = request.FILES.get('excel_file')
        user_id = request.data.get('user_id')
        
        usr_id=User.objects.get(id=user_id)
        
        

        if not uploaded_file:
            return JsonResponse({'error': 'No file was uploaded.'}, status=status.HTTP_BAD_REQUEST)

        if not uploaded_file.name.endswith('.xlsx'):
            return JsonResponse({'error': 'Only Excel files (xlsx) are supported.'}, status=status.HTTP_BAD_REQUEST)

        df = pd.read_excel(uploaded_file, engine='openpyxl')
        existing_emails = []
        for index, row in df.iterrows():
            
            # print(row[0])
            email = row.iloc[0]

            try:
                
                user_creation=UserCreation.objects.get(email=email)
            
                
                user=User.objects.get(id=user_creation.employee_user_id.id)
                user.active=False
                

                org=OrganizationDetails.objects.get(user_id=usr_id)
                
                org.number_of_employee-=1
                
                org.save()
                user.save()
                
                
                
                
                
            except ObjectDoesNotExist:
                print("-------ggg---------------")
                existing_emails.append(email)
                
                

                
        #print(existing_emails)
        # existing_emails_str = ", ".join(existing_emails) if existing_emails else "Nothing"
        return JsonResponse({
        "success": True,
        "status": status.HTTP_201_CREATED,                
        "message": "Users Created successfully",
        # "data":
        #     {
        #         "existing_email" : existing_emails_str
        #     }
        })




    @csrf_exempt
    def organizationRequestCount(self,request):
        try:
            
            total_requests = UserCreation.objects.filter(id = request.data['organization_id']).count()
            pending_requests = UserCreation.objects.filter(id = request.data['organization_id'], verified = 0).count()

           
            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "Request count fetch successfully",
                    "data":
                        {   
                            "orhanization" : request.data['organization_id'],
                            "pending_requests" : pending_requests,
                            "total_requests" : total_requests
                        }
                    }) 
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Fetch Request count",
                        "errors": str(e)
                        })


                
    @csrf_exempt
    def verifyUser(self,request):
        print("==================employee onboarding")
        try:
            
            create_user = UserCreation.objects.get(id = request.data['id'], processed = 2 )
            create_user.verified = 1
            create_user.processed = 3
            create_user.save()
            
            
            
            user = User.objects.get(id=create_user.employee_user_id.id)
            user.verified = 1
            user.save()
            
            t = threading.Thread(target=thread_to_add_personal_status, args=(user))
            t.setDaemon(True) 
            t.start() 
            
            # serialized_user = serialize('json', [user])  # Serialize the User object to JSON
            # user_data = serialized_user[1:-1]
            
            
            
            
            

            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User Verified successfully"
                    }) 
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Verify User",
                        "errors": str(e)
                        })
                
             
    @csrf_exempt
    def rejectUser(self,request):
        try:
            
            create_user = UserCreation.objects.get(id = request.data['id'], processed = 2 )
            create_user.verified = 2
            create_user.processed = 3
            create_user.save()
            
            user = User.objects.get(id=create_user.employee_user_id.id)
            user.verified = 2
            user.save()

            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User Rejected successfully",
                    "data":
                        {
                            "user_id" : create_user.employee_user_id.id
                        }
                    }) 
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Reject User",
                        "errors": str(e)
                        })
          
          
             
    @csrf_exempt
    def verifyDoctor(self,request):
        try:
            print(request.data['user_id'])
            
            user = User.objects.get(id=request.data['user_id'])
            user.verified = 1
            user.save()

            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User Verified Successfully",
                    "data":
                        {
                            "user_id" : user.id
                        }
                    }) 
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Verify User",
                        "errors": str(e)
                        })
                

                
                
    @csrf_exempt
    def emailVerification(self,request):
        try:
            
            user = User.objects.get(email = request.data['email'], firstname=  None )


            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "Email Verified Successfully",
                    "data":
                        {
                            "user_id" : user.id
                        }
                    }) 
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Email already in use",
                        "errors": str(e)
                        })
                
    @csrf_exempt
    def isProfileVerified(self,request):
        try:
            
            user = User.objects.get(id= request.data['user_id'], verified = 1)
            

            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User is Verified ",
                    "data":
                        {
                            "user_id" : user.id
                        }
                    }) 
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "User is not Verified ",
                        "errors": str(e)
                        })


    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('user_id', openapi.IN_QUERY, description="Parameter user_id", type=openapi.TYPE_INTEGER,default=2),
    ]) 
    @csrf_exempt
    def getUserData(self,request):
        
        added_user = User.objects.get(id=request.GET.get('user_id'))
        if request.GET.get('who_want')=="organization":
            org = get_object_or_404(OrganizationDetails, user_id=request.GET.get('user_id'))

            
            
            create_user = UserCreation.objects.filter(organization_id = org, verified = 1)
            serializer = UserCreationApprovedSerializers(create_user, many=True)
            verified_users = json.loads(json.dumps(serializer.data))
            verified_users_count = len(verified_users)
            
            create_user = UserCreation.objects.filter( organization_id = org, verified = 0).exclude(processed = 3)
            serializer = UserCreationSerializers(create_user, many=True)
            processed_users = json.loads(json.dumps(serializer.data))
            processed_users_count = len(processed_users)
            
            create_user = UserCreation.objects.filter(organization_id=org, verified=2)
            serializer = UserCreationSerializers(create_user, many=True)
            rejected_users = json.loads(json.dumps(serializer.data))
            rejected_users_count = len(rejected_users)
            
            create_user = UserCreation.objects.filter(organization_id=org)
            serializer = UserCreationSerializers(create_user, many=True)
            all_users = json.loads(json.dumps(serializer.data))
            all_users_count = len(all_users)
            
            # First, define the subquery to get the organization_id for the added_by user
            # employee_subquery = EmployeePersonalDetails.objects.filter(
            #     user_id=OuterRef('added_by')
            # ).values('organization_id')[:1]
            # print("🚀 ~ employee_subquery:", employee_subquery)
            
    
            
            outsider_user = OutsiderUser.objects.filter(
                organization= OrganizationDetails.objects.get(user_id =added_user.id )
            )
            serializer = OutsiderUserSerializers(outsider_user, many=True)
            outside_user = json.loads(json.dumps(serializer.data))
            outside_user_count = len(outside_user)
        else:
            create_user = UserCreation.objects.filter(created_by = request.GET.get('user_id'), verified = 1)
            serializer = UserCreationSerializers(create_user, many=True)
            verified_users = json.loads(json.dumps(serializer.data))
            verified_users_count = len(verified_users)
            
            create_user = UserCreation.objects.filter( created_by = request.GET.get('user_id'), verified = 0).exclude(processed = 3)
            serializer = UserCreationSerializers(create_user, many=True)
            processed_users = json.loads(json.dumps(serializer.data))
            processed_users_count = len(processed_users)
            
            create_user = UserCreation.objects.filter(created_by=request.GET.get('user_id'), verified=2)
            serializer = UserCreationSerializers(create_user, many=True)
            rejected_users = json.loads(json.dumps(serializer.data))
            rejected_users_count = len(rejected_users)
            
            create_user = UserCreation.objects.filter(created_by=request.GET.get('user_id'))
            serializer = UserCreationSerializers(create_user, many=True)
            all_users = json.loads(json.dumps(serializer.data))
            all_users_count = len(all_users)
            
            outsider_user = OutsiderUser.objects.filter(added_by=added_user)
            serializer = OutsiderUserSerializers(outsider_user, many=True)
            outside_user = json.loads(json.dumps(serializer.data))
            outside_user_count = len(outside_user)
        
        
        
        
        
        total_users_count = verified_users_count + processed_users_count
        
        if total_users_count > 0:
            all_users_percentage = int((total_users_count / all_users_count) * 100)
        else:
            all_users_percentage = 0

        if processed_users_count > 0:
            pending_users_percentage = int((processed_users_count / all_users_count) * 100)
        else:
            pending_users_percentage = 0 
       
        if verified_users_count > 0:
            approved_users_percentage = int((verified_users_count / all_users_count) * 100)
        else:
            approved_users_percentage = 0 
        
        if rejected_users_count > 0:
            rejected_users_percentage = int((rejected_users_count / all_users_count) * 100)
        else:
            rejected_users_percentage = 0
            
        if request.GET.get('who_want')=="organization":

            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User Details",
                    "data" : {
                        "verified_users" : verified_users,
                        "pending_users" : processed_users,
                        "total_employee_count":all_users_count,
                        "pending_users_count": processed_users_count,
                        "rejected_users_count":rejected_users_count,
                        "approved_user_count":verified_users_count,
                        "pending_users_percentage": pending_users_percentage,
                        "approved_users_percentage":approved_users_percentage,
                        "all_users_percentage":100,
                        "rejected_users_percentage":rejected_users_percentage,
                        "outsider_users":outside_user,
                        "outsider_users_count":outside_user_count
                        
                        
                    }
                    
                
                    }) 
        else:
            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User Details",
                    "data" : {
                        "verified_users" : verified_users,
                        "pending_users" : processed_users,
                        "rejected_users" : rejected_users,
                        "total_employee_count":all_users_count,
                        "pending_users_count": processed_users_count,
                        "rejected_users_count":rejected_users_count,
                        "approved_user_count":verified_users_count,
                        "pending_users_percentage": pending_users_percentage,
                        "approved_users_percentage":approved_users_percentage,
                        "all_users_percentage":100,
                        "rejected_users_percentage":rejected_users_percentage,
                        
                        "outsider_users":outside_user,
                        "outsider_users_count":outside_user_count
                    }
                    
                
                    }) 
            


    @csrf_exempt
    def getApprovedUser(self,request):
    
        org_instances = OrganizationDetails.objects.get(user_id=request.GET.get('user_id'))
        
        if request.GET.get('who_want')=="organization":
            if request.GET.get('which_one')=="all":
                create_user = UserCreation.objects.filter(organization_id = org_instances)
                serializer = UserCreationSerializersForUsers(create_user, many=True)
                users = json.loads(json.dumps(serializer.data))
            elif request.GET.get('which_one')=="approved":
                
                create_user = UserCreation.objects.filter(organization_id = org_instances, verified = 1)
                
                serializer = UserCreationSerializersForUsers(create_user, many=True)
                users = json.loads(json.dumps(serializer.data))
    
            elif request.GET.get('which_one')=="rejected":
    
            
                
                create_user = UserCreation.objects.filter(organization_id=org_instances, verified=2)
                
                serializer = UserCreationSerializersForUsers(create_user, many=True)
                users = json.loads(json.dumps(serializer.data))
                
            elif request.GET.get('which_one')=="pending":
                create_user = UserCreation.objects.filter(organization_id = org_instances, verified = 0).exclude(processed = 3)
                serializer = UserCreationSerializersForUsers(create_user, many=True)
                users = json.loads(json.dumps(serializer.data))
            
        return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,                
                "message": "User Details got",
                "data" : {
                    "users" : users                    
                }
                
                }) 
        
                
    
    
    @csrf_exempt
    def update_rejected_employee(self, request):
        try:
            user_id = request.POST.get('user_id')
            emp_id = request.POST.get('emp_id')
            org_instances = OrganizationDetails.objects.get(user_id=user_id)
            
    
            
            user_creation = UserCreation.objects.filter(id=emp_id, organization_id=org_instances).first()
    
            if user_creation:
                
                updateCol=User.objects.get(id=user_creation.employee_user_id.id)
                updateCol.verified = 1
                user_creation.verified = 1
                user_creation.processed = 3
                user_creation.save() 
                updateCol.save()
    
                return JsonResponse({
                    "success": True,
                    "status": 200,
                    "message": "User status updated successfully",
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "User not found",
                })
    
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 400,
                "message": str(e),
            })
    
                    
    
    
            
                
    @csrf_exempt
    def getData(self,request):
            
        create_user = UserCreation.objects.filter().values()
        print(create_user)


        return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,                
                "message": "User Verified successfully",
               
                }) 
    


    @csrf_exempt
    def send_invite(self,request):
        print("dfds")
        userDetails=UserCreation()
        try:
            token = generate_random_string(52)
            userDetails.token = token
            print(token)
            userAddressSerialData = InviteUserCreationSerializers(userDetails,data=request.data)
            
            try:
                
                if userAddressSerialData.is_valid(raise_exception=True):
                    sendOnBoardLink(request.data['email'], "https://www.ordinet.in/Digielves%20Project/Employee/index.html?access="+ str(token) )
                    userAddressSerialData.save()

                    return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User Created successfully",
                    "data":
                        {
                            "user_creation_id" : userDetails.id
                        }
                    })        
            except Exception as e:
                
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Create User",
                        "errors": str(e)
                        })
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Create User",
                        "errors": str(e)
                        })
    @csrf_exempt
    def test_mail(self,request):
        # user_id = request.GET.get('user_id')
        email = request.GET.get('email')
        try:
            token = generate_random_string(52)
            
            
            try:
                
                
                sendOnBoardLink(email, "https://www.ordinet.in/Digielves%20Project/Employee/index.html?access="+ str(token) )

                return JsonResponse({
                "success": True,
                
                })        
            except Exception as e:
                
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to send",
                        "errors": str(e)
                        })
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Create User",
                        "errors": str(e)
                        })
                        
                        
    @csrf_exempt
    def update_active_status(self, request):
        try:
            user_id = request.POST.get('user_id')   
            id = request.POST.get('id')
    
            user_check = User.objects.filter(id=user_id, user_role="Dev::Admin").exists()
    
            if user_check:
                user = get_object_or_404(User, id=id)
    
                # Check the user's role and update the active status accordingly
                if user.user_role == "Dev::Doctor" or user.user_role == "Dev::Organization":
                    # Logic for Dev::Doctor and Dev::Organization
                    if user.active:
                        user.active = not user.active
                        user.save()
                    else:
                        user.active = not user.active
                        user.save()
                    
                    if user.user_role == "Dev::Organization":
                        
                        org= OrganizationDetails.objects.get(user_id=user.id)
                                                
                        employees = EmployeePersonalDetails.objects.filter(organization_id=org.id)
                        
                        user_ids = [employee.user_id.id for employee in employees]

                        # Check the 'User' table for users with these user_ids
                        users = User.objects.filter(id__in=user_ids)
                        
                        # Now, the 'users' queryset contains the User records that match the user_ids from employees
                        print(users)
                        
                        for user in users:
                            # Toggle the 'active' field
                            if user.active:
                                
                                user.active = not user.active
                                user.save()
                            else:
                                user.active = not user.active
                                user.save()
                        
                        
    
                        return JsonResponse({
                            "success": True,
                            "status": 200,
                            "message": "User status updated successfully",

                        })
    
                    return JsonResponse({
                        "success": True,
                        "status": 200,
                        "message": "User status updated successfully",
                    })
    
                else:
                    return JsonResponse({
                        "success": False,
                        "status": 400,
                        "message": "You Don't have access to update status",
                    })
    
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 400,
                "message": str(e),
            })




    @csrf_exempt
    def update_active_status_emp(self,request):

        try:
        
            user_id = request.POST.get('user_id')
            emp_id = request.POST.get('employee_id')
            
            user_check = User.objects.filter(id=user_id,user_role="Dev::Organization")
            org=OrganizationDetails.objects.get(user_id=user_id)
                
            
            if user_check:

                user = get_object_or_404(User.objects.filter(Q(user_role="Dev::Employee") | Q(user_role="Prod::Employee")), id=emp_id)
                            
                if user.active:
                    
                    user.active = not user.active
                    user.save()
                    org.number_of_employee-=1
                    
                else:
                    user.active = not user.active
                    user.save()
                    org.number_of_employee+=1
                
                org.save()
    
                    
                   
        
                return JsonResponse({
                    "success": True,
                    "status": 200,
                    "message": "User status updated successfully",
                })
            else:
                return JsonResponse({
                "success": False,
                "status": 400,
                "message": "You Don't have access to update status",
            })
        
    
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 400,
                "message": str(e),
            })
                
    
    @csrf_exempt
    def deleteRequest(self,request):
        try:

            
            
            user_id=request.GET.get('user_id')
            user_creation_id=request.GET.get('created_id')
            user = User.objects.get(id=user_id)
            
            user_creation=UserCreation.objects.get(id=user_creation_id,employee_user_id=None) # currently not secure
            # check = UserCreation.objects.get(
            #         Q(created_by=user) | Q(created_by=created_by__usercreation__organization_id),id=check_id)
            user_creation.delete()
            

            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User Deleted successfully",
                    
                    }) 
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Delete User",
                        "errors": str(e)
                        })
                
         
    @csrf_exempt
    def resend_mail(self,request):

        try:
        
            user_id = request.POST.get('user_id')
            emp_id = request.POST.get('employee_id')
            
            user_check = User.objects.get(id=user_id,user_role="Dev::Organization")

                
            
            if user_check:
                
                org=OrganizationDetails.objects.get(user_id=user_id)
                user = UserCreation.objects.get(id=emp_id, organization_id=org)
                            
                t = threading.Thread(target=thread_to_send_invitation, args=(user.email,str(user.token)))
                t.setDaemon(True) 
                t.start() 
                return JsonResponse({
                    "success": True,
                    "status": 200,
                    "message": "Email sent successfully",
                })
            else:
                return JsonResponse({
                "success": False,
                "status": 400,
                "message": "You Don't have access",
            })
        
    
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 400,
                "message": str(e),
            })    
              
    @csrf_exempt
    def add_hierarchy(self,request):

        try:
        
            user_id = request.POST.get('user_id')
            emp_id = request.POST.get('employee_id')
            report_to_id = request.POST.get('report_to_id')
            hierarchy = request.POST.get('hierarchy')
            
            user_check = User.objects.get(id=user_id,user_role="Dev::Organization")

            
            if user_check:
                
                org=OrganizationDetails.objects.get(user_id=user_id)
                user = UserCreation.objects.get(id=emp_id, organization_id=org)
                
                try:
                    reporting=ReportingRelationship.objects.get(reporting_user=emp_id,reporting_to_user=report_to_id)
                    
                    return JsonResponse({
                        "success": False,
                        "status": 100,
                        "message":  f"The Reporting to with this email already exist",
                    })
                except Exception as e:
                    
                    try:
                        reporting=ReportingRelationship.objects.get(reporting_user=emp_id,hierarchy=hierarchy)
                        return JsonResponse({
                            "success": False,
                            "status": 100,
                            "message":  f"The specified hierarchy {hierarchy} is already assigned to another user.",
                        })
                    except Exception as e:
                        
                        user_report_to = UserCreation.objects.get(id=report_to_id, organization_id=org)
                        
                        user.reporting_to.add(user_report_to, through_defaults={'hierarchy': int(hierarchy)})
              
                            
                return JsonResponse({
                    "success": True,
                    "status": 200,
                    "message": "hierarchy added successfully",
                })
            else:
                return JsonResponse({
                "success": False,
                "status": 400,
                "message": "You Don't have access",
            })
        
    
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 400,
                "message": str(e),
            })
            
    @csrf_exempt
    def update_hierarchy(self, request):
        try:
            user_id = request.POST.get('user_id')
            emp_id = request.POST.get('employee_id')
            report_relationship_id = request.POST.get('report_relationship_id')
            hierarchy = int(request.POST.get('hierarchy'))

            user_check = User.objects.get(id=user_id, user_role="Dev::Organization")

            if user_check:
                org = get_object_or_404(OrganizationDetails, user_id=user_id)
                # this will also work but after that save* give problem
                # user_creation = get_object_or_404(UserCreation, id=emp_id, reporting_relationships__id=report_relationship_id)
                user_creation = get_object_or_404(UserCreation, id=emp_id)
                try:
                    reporting=ReportingRelationship.objects.get(reporting_user=emp_id,hierarchy=hierarchy)
                    
                    return JsonResponse({
                        "success": False,
                        "status": 100,
                        "message":  f"The specified hierarchy {hierarchy} is already assigned to another user.",
                    })
                except Exception as e:
                    
                    reporting_relationship = get_object_or_404(ReportingRelationship, id=report_relationship_id)
                    reporting_relationship.hierarchy = hierarchy
                    reporting_relationship.save()


                return JsonResponse({
                    "success": True,
                    "status": 200,
                    "message": "Hierarchy updated successfully",
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "You don't have access",
                })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": "User not found",
            })
        except UserCreation.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": "UserCreation not found",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 400,
                "message": str(e),
            })  
    
    @csrf_exempt
    def get_email(self, request):
        try:
            # Get the user_id and employee_id from the request parameters
            user_id = request.GET.get('user_id')
            emp_id = request.GET.get('employee_id')
            
            # Retrieve the User, OrganizationDetails, and UserCreation objects based on the provided IDs
            user = User.objects.get(id=user_id)
            org = OrganizationDetails.objects.get(user_id=user)
            user_create = UserCreation.objects.get(id=emp_id)
            
            # Find all UserCreation objects that have a reporting relationship with the provided employee_id
            # reporting = UserCreation.objects.filter(reporting_relationships__reporting_user_id=emp_id)
            
            # # Extract the unique reporting_to_user_ids from the queryset
            # reporting_to_user_ids = reporting.values_list('reporting_relationships__reporting_to_user_id', flat=True).distinct()
            
            # Find all UserCreation objects in the same organization but not in the reporting_to_user_ids list
            users = UserCreation.objects.filter(organization_id=org).exclude(id=user_create.id)
            
            # Serialize the user data
            userEmailSerialData = SendEmailserializers(users, many=True)
            
            # Return the serialized data as a JSON response
            return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "User get successfully",
                "data": userEmailSerialData.data
            }) 
        except Exception as e:
            # Handle any exceptions and return an error response
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST, 
                "errors": str(e)
            })

    
    @csrf_exempt
    def get_hierarchy(self,request):
        try:
      
            user_id=request.GET.get('user_id')
            employee_id=request.GET.get('employee_id')
            user = User.objects.get(id=user_id)
            users=UserCreation.objects.filter(id=employee_id)
            
            userHirarchy = GetHierarchySSerializers(users, many=True)

            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User hierarchy successfully",
                    "data":userHirarchy.data
                    }) 
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to get User hierarchy",
                        "errors": str(e)
                        })
    
    
    @csrf_exempt
    def delete_hierarchy(self, request):
        try:
            user_id = request.GET.get('user_id')
            emp_id = request.GET.get('employee_id')
            report_relationship_id = request.GET.get('report_relationship_id')

            user_check = User.objects.get(id=user_id, user_role="Dev::Organization")

            if user_check:
                org = get_object_or_404(OrganizationDetails, user_id=user_id)

                user_creation = get_object_or_404(UserCreation, id=emp_id)
                try:
                    reporting=ReportingRelationship.objects.get(id=report_relationship_id)
                    reporting.delete()
                    
                except Exception as e:
                    
                    return JsonResponse({
                        "success": False,
                        "status": 404,
                        "message": "Reporting Relationship not found",
                    })


                return JsonResponse({
                    "success": True,
                    "status": 200,
                    "message": "Hierarchy deleted successfully",
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "You don't have access",
                })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": "User not found",
            })
        except UserCreation.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": "UserCreation not found",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 400,
                "message": str(e),
            })  
    
    
def thread_to_send_invitation(email, token):

    sendOnBoardLink(email, "https://vibecopilot.ai/?access="+ str(token))

def thread_to_add_personal_status(user_id):

    for status_data in [
                            {"status_name": "Pending", "fixed_state": "Pending", "color": "#fb9e00", "order": 1},
                            {"status_name": "InProgress", "fixed_state": "InProgress", "color": "#8585e0", "order": 2},
                            {"status_name": "Completed", "fixed_state": "Completed", "color": "#009ce0", "order": 3},
                            {"status_name": "Closed", "fixed_state": "Closed", "color": "#33cc33", "order": 4}
                        ]:
                            PersonalStatus.objects.create(user_id=user_id, **status_data)
                            
                            

class TestMailClass(viewsets.ModelViewSet):
    
    permission_classes = [AllowAny]
    @csrf_exempt
    def test_mail(self,request):
        # user_id = request.GET.get('user_id')
        email = request.GET.get('email')
        try:
            token = generate_random_string(52)
            
            
            try:
                
                
                sendOnBoardLink(email, "https://www.ordinet.in/Digielves%20Project/Employee/index.html?access="+ str(token) )

                return JsonResponse({
                "success": True,
                
                })        
            except Exception as e:
                
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to send",
                        "errors": str(e)
                        })
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Create User",
                        "errors": str(e)
                        })