
import json
import logging
from configuration.gzipCompression import compress



from rest_framework import viewsets
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status

# Authentication Modules for rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.permissions import  IsAuthenticated ,AllowAny
from django.db.models import Q


from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from admin_app.seriallizers.consultation_seriallizers import ShowDoctorConsultationSerializerForAdmin

from digielves_setup.models import DoctorConsultation, User



logger = logging.getLogger('api_hits')
class DoctorConsultationAdminClass(viewsets.ModelViewSet):
  
    @csrf_exempt
    def GetDoctorConsultationForAdmin(self,request):  
        client_ip = get_client_ip(request)
                                                                                                                                                                                                      
        try:
            user_id = request.GET.get('user_id') 
            
            try:
                user_check = User.objects.get(id=user_id,user_role='Dev::Admin')
                print(user_check)
            except Exception as e:
                print(e)
                logger.info(f"API hit - {request.method}: {request.path} response: False (no permission)")   
            
                return JsonResponse({
                        "success": False,
                        "message": "You dont have permission"
                        })
              
            scheduledCount=DoctorConsultation.objects.filter( Q(status = 'Booked') | Q(status = 'Rescheduled'),confirmed = 1).count()
            


            cancelledCount=DoctorConsultation.objects.filter( status = 'Cancelled').count()
            


            completedCount=DoctorConsultation.objects.filter( status = 'Completed').count()


            consultationDetails=DoctorConsultation.objects.filter( status = 'Completed' )
            userSerialData = ShowDoctorConsultationSerializerForAdmin(consultationDetails, many=True)
            completed = json.loads(json.dumps(userSerialData.data))

            consultationDetails=DoctorConsultation.objects.filter(Q(status = 'Booked') | Q(status = 'Rescheduled'),confirmed = 1)
            userSerialData = ShowDoctorConsultationSerializerForAdmin(consultationDetails, many=True)
            upcoming = json.loads(json.dumps(userSerialData.data))

            consultationDetails=DoctorConsultation.objects.filter(status = 'Cancelled')
            userSerialData = ShowDoctorConsultationSerializerForAdmin(consultationDetails, many=True)
            cancelled = json.loads(json.dumps(userSerialData.data))
            
            total = scheduledCount + cancelledCount + completedCount
            logger.info(f"API hit - {request.method}: {request.path} response: True from client ip :{client_ip}")   
            
            response={
            "success": True,
            "status": status.HTTP_200_OK,                
            "message": " Consultation List",
            'data':
                {
                  'appointments_count' : 
                          {
                            'total' : total,
                            'scheduled': scheduledCount,
                            'cancelled': cancelledCount,
                            'completed': completedCount,
                          },
                    'appointments_percentage' : 
                          {
                            'scheduled': 0 if scheduledCount == 0 else round(((scheduledCount)/total) * 100,2),
                            'cancelled': 0 if cancelledCount == 0 else round(((cancelledCount)/total) * 100,2) ,
                            'completed': 0 if completedCount == 0 else round(((completedCount)/total) * 100,2)  ,
                          },
                  
                  'appointments':{
                    'completed': completed,
                    'upcoming' : upcoming ,
                    'cancelled': cancelled
        }
                    


                },
            }
            return compress(response)
                 
      
        except Exception as e:
            logger.info(f"API hit - {request.method}: {request.path} response: False ({e})")   
            return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Fetch List",
                        "errors": str(e)
                        })

def get_client_ip(request):
    """
    Get the client's IP address from the request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip