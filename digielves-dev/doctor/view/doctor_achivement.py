import base64
import json
import random
from django.shortcuts import render
from configuration.authentication import JWTAuthenticationUser
from configuration.gzipCompression import compress
from digielves_setup.validations import is_valid_image
from rest_framework import viewsets
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status

# Authentication Modules for rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.permissions import  IsAuthenticated ,AllowAny
from django.db.models import Max

# Application Response Serializer 

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from digielves_setup.models import  DoctorAchivement
from doctor.seriallizers.achievements import AddDoctorAchivementSerializer,DoctorAchivementSerializer

class DoctorAchievemnetsClass(viewsets.ModelViewSet):

    authentication_classes = [JWTAuthenticationUser]
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]

    throttle_classes = [AnonRateThrottle,UserRateThrottle]

    serializer_class = AddDoctorAchivementSerializer

    @csrf_exempt
    def addDoctorAchivement(self,request):

        doctorAchivement=DoctorAchivement()
        try:
            
            doctorAchivementSerialData = AddDoctorAchivementSerializer(doctorAchivement,data=request.data)
            try:
            
                if doctorAchivementSerialData.is_valid(raise_exception=True):
                        doctorAchivementSerialData.save()


                        user_folder = settings.MEDIA_ROOT
                try:
                
                    attachment = request.data['achivement_file']
                    if len(attachment)  > 20:
                        filename =  '/doctor/achivement/doctor_' + ''.join(random.choices('0123456789', k=12))  +   str(doctorAchivement.id) + '.jpeg'
                        with open(user_folder + filename, 'wb') as f:
                            f.write(attachment.read())

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
                "data" :  {
                    "achievement_id" :  doctorAchivement.id
                }
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
                
    # Client Registration API
    @csrf_exempt
    def getAchievements(self,request):
        print(request.GET.get('partner_id'))
        
        try:
            DoctorAchivement.objects.filter(user_id = request.GET.get('user_id')).values('id')[0] 
            partner_images=DoctorAchivement.objects.filter(user_id = request.GET.get('user_id')) 

            serializer = DoctorAchivementSerializer(partner_images, many=True)
            partner_images = json.loads(json.dumps(serializer.data))
            response = {
                    "success": True,
                    "status": status.HTTP_200_OK, 
                    "message": "Doctor Achivement fetched successfully",
                    "data": partner_images
                    }

            return compress(response)     

                  
        except Exception as e:
                response = {
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to fetch Doctor Achivement",
                        "errors": str(e)
                        }

                return compress(response)                
     
    
    @csrf_exempt
    def deleteAchievements(self,request):
        try:
            data = DoctorAchivement.objects.get(id=request.GET.get('achievement_id'))
            data.delete()
            # print('gaurav')
            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Doctor Achivement deleted successfully",
            }
            return compress(response)     

        except DoctorAchivement.DoesNotExist:
            response = {
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Doctor Achivement not found",
            }
            return compress(response)     

        except Exception as e:
            response = {
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to delete Doctor Achivement",
                "errors": str(e),
            }
            return compress(response)     


