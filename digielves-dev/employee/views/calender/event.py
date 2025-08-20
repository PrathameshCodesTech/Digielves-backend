
from django.http import JsonResponse

from configuration.gzipCompression import compress
from digielves_setup.models import Events, User
from employee.seriallizers.calender.event_seriallizers import EventSerializer

from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.conf import settings
import os

class EventsViewset(viewsets.ModelViewSet):


    serializer_class = EventSerializer

    @csrf_exempt
    def addEvent(self,request):

        try:
            event_serial_data = EventSerializer(data=request.data)
            if event_serial_data.is_valid():
                event = event_serial_data.save()

                guest_ids = request.data.get('guest_ids', ',')
                guest_user_ids = [int(id) for id in guest_ids.split(',') if id]
                guest_users = User.objects.filter(id__in=guest_user_ids)
                event.guest.set(guest_users)

                if 'attachment' in request.FILES:
                    attachment = request.FILES['attachment']
                    filename =  '/employee/event/' + attachment.name
                    user_folder = settings.MEDIA_ROOT 
                    with open(user_folder + filename, 'wb') as f:
                        f.write(attachment.read())
                    fs = FileSystemStorage(location=settings.MEDIA_ROOT)
                    filename = fs.save(attachment.name, attachment)
                    event.attachment = os.path.join('/employee/event/', filename) 


                event.save()

                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Event added successfully",
                })

            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid data",
                "errors": event_serial_data.errors
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to add event",
                "errors": str(e)
            })