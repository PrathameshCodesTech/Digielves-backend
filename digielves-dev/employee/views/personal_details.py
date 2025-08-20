import base64
import json
import random
from django.shortcuts import render
from configuration.authentication import JWTAuthenticationUser
from configuration.gzipCompression import compress
from digielves_setup.models import EmployeePersonalDetails, Notification, User, UserCreation, notification_handler
from digielves_setup.validations import is_valid_image
from employee.seriallizers.personal_details_seriallizer import EmployeePersonalDetailsSerializer,UpdateEmployeePersonalDetailsSerializer


from rest_framework import viewsets
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status

from rest_framework.generics import GenericAPIView

# Authentication Modules for rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.permissions import  IsAuthenticated ,AllowAny

from django.db.models import Max

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


from rest_framework import generics

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
class EmployeeDetailsClass(viewsets.ModelViewSet):


    # authentication_classes = [JWTAuthenticationUser]
    # permission_classes = [IsAuthenticated ]
    # # permission_classes = [AllowAny]
    # throttle_classes = [AnonRateThrottle,UserRateThrottle]

    serializer_class =EmployeePersonalDetailsSerializer

    # Client Registration API 
    @csrf_exempt
    def addEmployeeDetails(self,request):
    
        
        

        employeeDetails=EmployeePersonalDetails()
        try:

            
            userSerialData = EmployeePersonalDetailsSerializer(employeeDetails,data=request.data)
            try:

                
                if userSerialData.is_valid(raise_exception=True):
                    print("------")
                    print(request.data['user_id'] )
                    print("------")
                    create_user = UserCreation.objects.filter( employee_user_id = request.data['user_id'] )
                   
                    first_user_creation = create_user[0] 

                    print(first_user_creation)
                    print("Organization ID:", first_user_creation.organization_id)
                    print("Created By:", first_user_creation.created_by)
                    
                    print("Email:", first_user_creation.email)
                    first_user_creation.processed = 2
                    first_user_creation.save()
                    
                    userSerialData.save()
                    

                    Employee_personal = EmployeePersonalDetails.objects.get(id=employeeDetails.id)
                    
                    Employee_personal.organization_id=first_user_creation.organization_id
                    Employee_personal.organization_location=first_user_creation.organization_location
                    
                    Employee_personal.save()
                    
                    user_folder = settings.MEDIA_ROOT
                    try:

                        image = request.FILES.get('profile_picture')
                        print(image)

                        if image:
                            

                            filename =  '/employee/profile/employee_' + ''.join(random.choices('0123456789', k=8))  +   str(employeeDetails.id) + '_' + image.name
                            with open(user_folder + filename, 'wb') as f:
                                f.write(image.read())


                            # Create and save the png file 
                            EmployeeProfile = EmployeePersonalDetails.objects.get(id=employeeDetails.id)
                            EmployeeProfile.profile_picture = filename
                            EmployeeProfile.save()
                    except Exception as e:

                        pass
                    
                    
                    
                    try:
                        post_save.disconnect(notification_handler, sender=Notification)
                        notification = Notification.objects.create(
                            user_id=request.user,
                            where_to="user_created",
                            notification_msg=f"New user on boarded with email '{first_user_creation.email}'. Please review and approve or reject.",
                            action_content_type=ContentType.objects.get_for_model(UserCreation),
                            action_id=User.objects.get(id=request.data['user_id']).id
                        )
                        
                        notification.notification_to.set([first_user_creation.created_by])
                        post_save.connect(notification_handler, sender=Notification)
                        post_save.send(sender=Notification, instance=notification, created=True)
                       
                        
                    except Exception as e:
                        print("Notification creation failed:", e)

                            

                    return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                 
                    "message": "Employee Details added successfully",
                    'data':
                        {
                            'employee_user_id': request.data['user_id']
                        }
                    })        
            except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to add Employee Details",
                        "errors": str(e)
                        })
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to add Employee Details",
                        "errors": str(e)
                        })

    # Client Registration API 
    @csrf_exempt
    def updateEmployeeDetails(self,request):
        print("--------------------------------")
        print(request.data)
        try:
            employeeDetails=EmployeePersonalDetails.objects.get(user_id=request.data['user_id'])
            userSerialData = UpdateEmployeePersonalDetailsSerializer(employeeDetails,data=request.data)
            try:
                
                if userSerialData.is_valid(raise_exception=True):

                    userSerialData.save()
   
                    
                    try:
                        user_folder = settings.MEDIA_ROOT

                                
                        image =request.POST['profile_picture']

                        if len(image)  > 5:

                            filename =  '/employee/profile/employee_' + ''.join(random.choices('0123456789', k=12))  +   str(employeeDetails.id) + '.jpeg'
                            with open(user_folder + filename, 'wb') as f:
                                f.write(image.read())

                            # Create and save the png file 
                            EmployeeProfile = EmployeePersonalDetails.objects.get(id=employeeDetails.id)
                            EmployeeProfile.profile_picture = filename
                            EmployeeProfile.save()
                    except Exception as e:

                            pass

                    return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "Employee Details added successfully",
                    'data':
                        {
                            'user_id': request.data['user_id']
                        }
                    })
                            
            except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to add Employee Details",
                        "errors": str(e)
                        })
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to add Employee Details",
                        "errors": str(e)
                        })


    # Client Registration API
    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('user_id', openapi.IN_QUERY, description="User ID parameter", type=openapi.TYPE_INTEGER,default=2)
    ]) 
    @csrf_exempt
    def getEmployeeDetails(self,request):
        print("--------------------------------")
        try:
            EmployeePersonalDetails.objects.filter(user_id = request.GET.get('user_id')).values('id')[0] 
            employeeDetails=EmployeePersonalDetails.objects.filter(user_id=request.GET.get('user_id')) 

            serializer = EmployeePersonalDetailsSerializer(employeeDetails, many=True)
            details = json.loads(json.dumps(serializer.data))
            response = {
                    "success": True,
                    "status": status.HTTP_200_OK, 
                    "message": "Employee details fetched successfully",
                    "data": details
                    }

            return  (response)     

                  
        except Exception as e:
                response = {
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to fetch details",
                        "errors": str(e)
                        }

                return compress(response)     

        



    @csrf_exempt
    def updateProfilePicture(self,request):  
        print(request.data)
        try:
            employeeDetails=EmployeePersonalDetails.objects.get(user_id=request.data['user_id'])
            user_folder = settings.MEDIA_ROOT
            image = request.data['image']

            if len(image)  > 5:

                filename =  '/employee/profile/employee_' + ''.join(random.choices('0123456789', k=12))  +   str(employeeDetails.id) + '.jpeg'
                with open(user_folder + filename, 'wb') as f:
                    f.write(image.read())

                # Create and save the png file 
            employeeDetails.profile_picture = filename
                
            if is_valid_image(user_folder + filename):
                employeeDetails.save()

                    
                response = {
                        "success": True,
                        "status": status.HTTP_200_OK, 
                        "message": "Employee profile updated successfully",
                        "data": {
                            'employee_details_id' : request.data['user_id']
                        }
                }
                return compress(response)
            else:
                response = {
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to update partner profile picture",
                        "errors": str(e)
                        }

                return compress(response)

        except Exception as e:
                response = {
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to update partner profile picture",
                        "errors": str(e)
                        }

                return compress(response)
            
            
    @csrf_exempt
    def getProfilePicture(self,request):
        print("--------------------------------")
        try:
            EmployeePersonalDetails.objects.filter(user_id = request.GET.get('user_id')).values('id')[0] 
            employeeDetails=EmployeePersonalDetails.objects.get(user_id=request.GET.get('user_id')) 

            
            response = {
                    "success": True,
                    "status": status.HTTP_200_OK, 
                    "message": "Profile picture fetched successfully",
                    "data": employeeDetails.profile_picture
                    }

            return compress(response)     

                  
        except Exception as e:
                response = {
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to fetch Profile picture",
                        "errors": str(e)
                        }

                return compress(response)     

        




