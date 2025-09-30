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
from digielves_setup.models import  DoctorPrescriptions, Medicines
from doctor.seriallizers.prescription_serillizer import MedicinesSerializer, ShowDoctorPrescriptionsSerializer,DoctorPrescriptionsSerializer

import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

class DoctorPrescriptionClass(viewsets.ModelViewSet):

    # authentication_classes = [JWTAuthenticationUser]
    # # permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]

    # throttle_classes = [AnonRateThrottle,UserRateThrottle]

    serializer_class = DoctorPrescriptionsSerializer

    @csrf_exempt
    def addDoctorPrescription(self,request):

        doctorPrescription=DoctorPrescriptions()
        try:
            
            doctorPrescriptionSerialData = DoctorPrescriptionsSerializer(doctorPrescription,data=request.data)
            try:
            
                if doctorPrescriptionSerialData.is_valid(raise_exception=True):
                        doctorPrescriptionSerialData.save()


                 

                return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,                
                "message": "Prescription added successfully",
                "data" :  {
                    "achievement_id" :  doctorPrescription.id
                }
                })        
            except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to add Prescription",
                        "errors": str(e)
                        })
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to add Prescription",
                        "errors": str(e)
                        })
                
    # Client Registration API
    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('consultation_id', openapi.IN_QUERY, description="Parameter consultation_id", type=openapi.TYPE_INTEGER,default=2),
    openapi.Parameter('user_id', openapi.IN_QUERY, description="Parameter user_id", type=openapi.TYPE_INTEGER,default=2),

    ]) 
    @csrf_exempt
    def getDoctorPrescription(self, request):
        print(request.GET.get('consultation_id'))
        try:
            user_id = request.GET.get('user_id')
            consultation_id = request.GET.get('consultation_id')
            doctor_prescriptions = DoctorPrescriptions.objects.filter(consultation_id=consultation_id)

            #if doctor_prescriptions.exists():
            serializer = ShowDoctorPrescriptionsSerializer(doctor_prescriptions, many=True)
            partner_images = json.loads(json.dumps(serializer.data))
            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Doctor Achievement fetched successfully",
                "data": partner_images
            }
#            else:
#                response = {
#                    "success": True,
#                    "status": status.HTTP_200_OK,
#                    "message": "Doctor Achievement not found for the given consultation_id",
#                     "data": partner_images
#                }

            return compress(response)     

        except Exception as e:
            response = {
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to fetch Doctor Achievement",
                "errors": str(e)
            }

            return compress(response)

    # @csrf_exempt
    # def getDoctorPrescription(self,request):
    #     print(request.GET.get('partner_id'))
        
    #     try:
    #         DoctorPrescriptions.objects.filter(consultation_id = request.GET.get('consultation_id')).values('id')[0] 
    #         partner_images=DoctorPrescriptions.objects.filter(consultation_id = request.GET.get('consultation_id')) 

    #         serializer = ShowDoctorPrescriptionsSerializer(partner_images, many=True)
    #         partner_images = json.loads(json.dumps(serializer.data))
    #         response = {
    #                 "success": True,
    #                 "status": status.HTTP_200_OK, 
    #                 "message": "Doctor Achivement fetched successfully",
    #                 "data": partner_images
    #                 }

    #         return compress(response)     

                  
    #     except Exception as e:
    #             response = {
    #                     "success": False,
    #                     "status": status.HTTP_400_BAD_REQUEST, 
    #                     "message": "Failed to fetch Doctor Achivement",
    #                     "errors": str(e)
    #                     }

    #             return compress(response)     
     
    
class MedicineClass(viewsets.ModelViewSet):
    
    
    @csrf_exempt
    def AddMedicine(self, request):
        if 'file' in request.FILES:
            # Handle file upload with multiple medicines
            uploaded_file = request.FILES.get('file')

            if not uploaded_file.name.endswith('.xlsx'):
                return JsonResponse({'error': 'Only Excel files (xlsx) are supported.'}, status=status.HTTP_BAD_REQUEST)

            df = pd.read_excel(uploaded_file, engine='openpyxl')
            existing_medicine = []

            for index, row in df.iterrows():
                medicine = row.iloc[0]

                try:
                    Medicines.objects.get(medicine_name=medicine)
                    existing_medicine.append(medicine)
                except ObjectDoesNotExist:
                    medicines = Medicines()
                    try:
                        medicines.medicine_name = medicine
                        medicines.save()
                    except Exception as e:
                        return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Failed to Add Medicine",
                            "errors": str(e)
                        })

            existing_medicines_str = ", ".join(existing_medicine) if existing_medicine else "Nothing"
            return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Medicine(s) added successfully",
                "data": {
                    "existing_medicine": existing_medicines_str
                }
            })

        elif 'medicine_name' in request.data:
            # Handle adding a single medicine by name
            medicine_name = request.data.get('medicine_name')

            try:
                Medicines.objects.get(medicine_name=medicine_name)
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Medicine already exists",
                })
            except ObjectDoesNotExist:
                try:
                    medicines = Medicines()
                    medicines.medicine_name = medicine_name
                    medicines.save()
                    return JsonResponse({
                        "success": True,
                        "status": status.HTTP_201_CREATED,
                        "message": "Medicine added successfully",
                        
                    })
                except Exception as e:
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Failed to Add Medicine",
                        "errors": str(e)
                    })

        else:
            return JsonResponse({'error': 'Invalid request. Please provide either a file or a medicine name.'}, status=status.HTTP_BAD_REQUEST)

        
        
    @csrf_exempt
    def getMedicine(self, request):
        
        try:
            user_id = request.GET.get('user_id')
            medicines = Medicines.objects.all()

            
            serializer = MedicinesSerializer(medicines, many=True)
           
            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "medicines",
                "data": serializer.data
            }


            return compress(response)     

        except Exception as e:
            response = {
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to fetch Medicines",
                "errors": str(e)
            }

            return JsonResponse(response)