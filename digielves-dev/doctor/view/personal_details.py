import base64
import json
import random
from django.shortcuts import render
from configuration.authentication import JWTAuthenticationUser
from configuration.gzipCompression import compress
from digielves_setup.validations import is_valid_image
from doctor.seriallizers.doctor_serillizer import DoctorAchivementSerializer, UpdateDoctorPersonalDetailsSerializer, DoctorPersonalDetailsSerializer,RegNdDoctorPersonalDetailsSerializer, UserRegistraionSerializer
from rest_framework import viewsets
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status

# Authentication Modules for rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.permissions import  IsAuthenticated ,AllowAny
from django.db.models import Max

from configuration.onboardingEmail import sendMail
# Application Response Serializer 
import bcrypt
import csv
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from digielves_setup.models import Address, DoctorAchivement, DoctorPersonalDetails, User
from digielves_setup.seriallizers.address import UserAddressSerializers

class DoctorDetailsClass(viewsets.ModelViewSet):

    # authentication_classes = [JWTAuthenticationUser]
    # # permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]

    # throttle_classes = [AnonRateThrottle,UserRateThrottle]
    serializer_class = DoctorPersonalDetailsSerializer

        
    # Client Registration API 
    @csrf_exempt
    def addDetails(self, request):
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
            print("-----heyy")
    
            if user.is_valid():
                print("-----heyy2")
                try:
                    response = user.save()
    
                    personalDetails = DoctorPersonalDetails()
    
                    user_instance = User.objects.get(id=user_object.id)
                    personalDetails.user_id = user_instance
    
                    try:
                        print("heyyyy1")
                        userAddressSerialData = RegNdDoctorPersonalDetailsSerializer(personalDetails, data=request.data)
                        print("heyyyy2")
    
                        if userAddressSerialData.is_valid(raise_exception=True):
                            print("heyyyy3")
                            userAddressSerialData.save()
                            
                            email = request.data['email']
                            print(email)
                            
                            #sendMail(email , "Email :" + str(email) , "Password: "+str(request.data['password']))
                            sendMail(email , f"Email: {email}, Password: {str(request.data['password'])}")
                            
                            print("hmmm1")
                            user_folder = settings.MEDIA_ROOT
    
                            try:
                                profile_picture = request.FILES.get('profile_picture')
    
                                if profile_picture:
                                    filename = '/doctor/profile/doctor_' + ''.join(random.choices('0123456789', k=8)) + str(personalDetails.id) + '_' + profile_picture.name
    
                                    with open(user_folder + filename, 'wb') as f:
                                        f.write(profile_picture.read())
    
                                    DoctorProfile = DoctorPersonalDetails.objects.get(id=personalDetails.id)
                                    DoctorProfile.profile_picture = filename
                                    DoctorProfile.save()
                                    
                                    
                            except Exception as e:
                                print(str(e))
                                pass
    
                            return JsonResponse({
                                "success": True,
                                "status": status.HTTP_201_CREATED,
                                "message": "Personal Details added successfully",
                               
                            })
                    except Exception as e:
                        user_instance.delete()
                        return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Failed to add Personal Details",
                            "errors": str(e)
                        })
                except Exception as e:
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Failed to add Personal Details",
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
                "message": "Failed to add Personal Details",
                "errors": str(e)
            })


        

    # Client Registration API 
    @csrf_exempt
    def updateDetails(self,request):

        try:
            personalDetails=DoctorPersonalDetails.objects.get(user_id=request.data['doctor_user_id'])

            userAddressSerialData = UpdateDoctorPersonalDetailsSerializer(personalDetails,data=request.data)
            try:
                if userAddressSerialData.is_valid(raise_exception=True):
                    userAddressSerialData.save()
                    user_folder = settings.MEDIA_ROOT
                try:
                    print("----------------------------")
                    profile_picture = request.FILES.get('profile_picture')
                    
                    print("----------------------------")
                    print(profile_picture)
            
                    if profile_picture:

                        filename = '/doctor/profile/doctor_' + ''.join(random.choices('0123456789', k=8)) + str(personalDetails.id) + '_' + profile_picture.name
                        with open(user_folder + filename, 'wb') as f:
                            f.write(profile_picture.read())
                    

                        # Create and save the png file 
                        DoctorProfile = DoctorPersonalDetails.objects.get(id=personalDetails.id)
                        DoctorProfile.profile_picture = filename
                        DoctorProfile.save()
                except Exception as e:
                    print(str(e))
                    pass

                return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,                
                "message": "Personal Details updated successfully",
                "data":
                    {
                        'doctor_user_id' : request.data['doctor_user_id']
                    }
                })        
            except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to update Personal Details",
                        "errors": str(e)
                        })
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to update Personal Details",
                        "errors": str(e)
                        })
       
    # Client Registration API 
    @csrf_exempt
    def getDetails(self,request):
        print("--------------------------------")
        try:
            DoctorPersonalDetails.objects.filter(user_id = request.GET.get('doctor_user_id')).values('id')[0] 
            employeeDetails=DoctorPersonalDetails.objects.filter(user_id=request.GET.get('doctor_user_id')) 

            serializer = DoctorPersonalDetailsSerializer(employeeDetails, many=True)
            details = json.loads(json.dumps(serializer.data))
            response = {
                    "success": True,
                    "status": status.HTTP_200_OK, 
                    "message": "Doctor details fetched successfully",
                    "data": details
                    }

            return compress(response)     

                  
        except Exception as e:
                response = {
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to fetch Doctor details",
                        "errors": str(e)
                        }

                return compress(response)     

        
       
 
    @csrf_exempt
    def updateProfilePicture(self,request):  
        try:
            employeeDetails=DoctorPersonalDetails.objects.get(user_id=request.data['doctor_user_id'])
            user_folder = settings.MEDIA_ROOT
            image = request.data['image']
            if len(image)  > 20:
                # imgdata = base64.b64decode(request.POST['image'])
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
                            'doctor_id' : request.data['doctor_user_id']
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
            DoctorPersonalDetails.objects.filter(user_id = request.GET.get('doctor_user_id')).values('id')[0] 
            employeeDetails=DoctorPersonalDetails.objects.get(user_id=request.GET.get('doctor_user_id')) 

            
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

        


    @csrf_exempt
    def addDoctorAchivement(self,request):
        print("--------------------------------")
        print(request.data)
        doctorAchivement=DoctorAchivement()
        try:
            
            doctorAchivementSerialData = DoctorAchivementSerializer(doctorAchivement,data=request.data)
            try:
            
                if doctorAchivementSerialData.is_valid(raise_exception=True):
                        doctorAchivementSerialData.save()


                        user_folder = settings.MEDIA_ROOT
                try:
                
                    attachment = request.POST['achivement_file']
                    if len(attachment)  > 20:
                        imgdata = base64.b64decode(request.POST['achivement_file'])
                        filename =  '/doctor/achivement/doctor_' + ''.join(random.choices('0123456789', k=12))  +   str(doctorAchivement.id) + '.jpeg'
                        with open(user_folder + filename, 'wb') as f:
                            f.write(imgdata)

                        # Create and save the png file 
                        DoctorAchivements = DoctorAchivement.objects.get(id=doctorAchivement.id)
                        DoctorAchivements.profile_picture = filename
                        DoctorAchivements.save()
                except Exception as e:
                    return JsonResponse({
                    "success": True,
                    "status": status.HTTP_400_BAD_REQUEST,                
                    "message": "Failed to add Achievement file",
                    "error":str(e)
                    })  

                return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,                
                "message": "Achivement added successfully",
                })        
            except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to add Achivement",
                        "errors": str(e)
                        })
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to add Achivement",
                        "errors": str(e)
                        })