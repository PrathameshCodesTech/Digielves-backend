from django.http import JsonResponse

from configuration.gzipCompression import compress
from digielves_setup.models import DoctorConsultation
from doctor.seriallizers.calender_seriallizers import calenderDoctorConsultationseriallizers
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.conf import settings
import random
import os

class CalenderViewSet(viewsets.ModelViewSet):
    # serializer_class = HelpdeskCreateSerializer


    @csrf_exempt
    def get_calender_events(self,request):
        try:
            doctor_id = request.GET.get('doctor_id')
            queryset = DoctorConsultation.objects.filter(doctor_id=doctor_id)
            
            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "Calendar Details Getting successfully",
                    'data': calenderDoctorConsultationseriallizers(queryset,many=True).data
                    })
        except Exception as e:
            return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST, 
                    "message": "Failed to Get Calendar Details",
                    "errors": str(e)
                    })