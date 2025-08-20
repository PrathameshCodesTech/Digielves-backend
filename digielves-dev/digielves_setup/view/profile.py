

from django.http import JsonResponse

from configuration.gzipCompression import compress
from digielves_setup.models import DoctorPersonalDetails, EmployeePersonalDetails, OrganizationDetails, User
from digielves_setup.seriallizers.profile_seriallizers import DoctorPersonalDetailsSerializer, EmployeePersonalDetailsSerializer, OrganizationDetailsSerializer, UserSerializer, UserUpdateSerializer

from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.conf import settings
import random
import os

class ProfileViewSet(viewsets.ModelViewSet):
    # serializer_class = HelpdeskCreateSerializer


    @csrf_exempt
    def get_profile(self,request):
        try:
            type_param = request.GET.get('type')
            user_id = request.GET.get('user_id')


            if type_param == 'doctor':
                
                doctor_data = DoctorPersonalDetails.objects.filter(user_id=user_id)

                return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,                
                "message": "Profile Getting successfully",
                'data': DoctorPersonalDetailsSerializer(doctor_data, many=True).data
                })

            elif type_param == 'organization':
                
                org_data = OrganizationDetails.objects.filter(user_id=user_id)
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "Profile Getting successfully",
                    'data': OrganizationDetailsSerializer(org_data, many=True).data
                    })
            
            else:
                employe_data = EmployeePersonalDetails.objects.filter(user_id=user_id)
            
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "Profile Getting successfully",
                    'data': EmployeePersonalDetailsSerializer(employe_data, many=True).data
                    })
  
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=404)
        
        
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Get Profile Details",
                        "errors": str(e)
                        })
        
    
    @csrf_exempt
    def update_user_profile(self,request):
        user_id = request.data.get('user_id')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            employee_details = EmployeePersonalDetails.objects.get(user_id=user_id)
        except EmployeePersonalDetails.DoesNotExist:
            employee_details = None

        if 'profile' in request.FILES:
            profile_picture = request.FILES['profile']
        
            if profile_picture:
                user_folder = settings.MEDIA_ROOT
                
                filename = f'/employee/profile/employee_{user_id}_{profile_picture.name.split(".")[0]}.{profile_picture.name.split(".")[-1]}' 
                
                file_path = user_folder + filename
        
                
                if employee_details and employee_details.profile_picture:
                    existing_profile_path = user_folder + employee_details.profile_picture
                    if os.path.exists(existing_profile_path):
                        os.remove(existing_profile_path)
        
                with open(file_path, 'wb') as f:
                    f.write(profile_picture.read())
        
                if employee_details:
                    employee_details.profile_picture = filename
                    employee_details.save()

        else:
            email = request.data.get('email')
            phone_no = request.data.get('phone_no')
            date_of_birth = request.data.get('date_of_birth')

            serializer = UserUpdateSerializer(data=request.data)

            if serializer.is_valid():
                if 'email' in serializer.validated_data:
                    user.email = serializer.validated_data['email']
                if 'phone_no' in serializer.validated_data:
                    user.phone_no = serializer.validated_data['phone_no']

                user.save()

                if employee_details:
                    if phone_no:
                        employee_details.phone_no = phone_no
                    if date_of_birth:
                        employee_details.date_of_birth = date_of_birth

                    employee_details.save()

                return JsonResponse({
                    "success": True,
                    "message": "User profile updated successfully."
                }, status=status.HTTP_200_OK)

            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({
            "success": True,
            "message": "User profile updated successfully."
        }, status=status.HTTP_200_OK)




        
