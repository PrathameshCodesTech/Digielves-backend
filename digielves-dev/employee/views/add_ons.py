
from django.http import JsonResponse

from configuration.gzipCompression import compress
from digielves_setup.models import Events, Meettings, Tasks, User, DoctorConsultation, DoctorConsultationDetails, EmployeePersonalDetails
from employee.seriallizers.calender.calender_seriallizaers import  CombinedEventMeetingSerializerOnly, EventCalenderDashboardSerializer, EventCalenderSerializer, MeetingCalenderDashboardSerializer, MeetingCalenderSerializer, TasksCalenderSerializer
from employee.seriallizers.calender.event_seriallizers import EventSerializer

from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from employee.seriallizers.calender.meeting_seriallizers import MeetingSerializer, Meettingerializer, MeetingGetSerializer, MeettingSummerySerializer
from django.db.models import Q
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication
from employee.seriallizers.add_ons_seriallizers import ShowDoctorConsultationSerializer, CombinedEventMeetingSerializerForAddOns
import json

class AddOnsMeetingNdTaskViewset(viewsets.ModelViewSet):


    serializer_class = Meettingerializer
    #authentication_classes = []

    permission_classes = [AllowAny]
    

   
    @csrf_exempt
    def getAddOnsDetails(self, request):
        try:
            
            email = request.GET.get('email')
            

            user = User.objects.get(email=email) 
            try:
                print(user)
                print("---------")
                emp_details=EmployeePersonalDetails.objects.get(user_id=user.id)
                print(emp_details)
            
            except Exception as e:
                print(e)
                print("---------")
            
                
            #guest_events = Events.objects.filter(Q(user_id=user) | Q(guest=user)).distinct().order_by('-created_at')
            participant_meetings = Meettings.objects.filter(Q(user_id=user) | Q(participant=user)).distinct().order_by('-created_at')
            user_tasks = Tasks.objects.filter(Q(created_by=user) | Q(assign_to=user)).distinct()
            
            events_and_meetings = list(participant_meetings) + list(user_tasks)


            
            combined_serializer = CombinedEventMeetingSerializerForAddOns(events_and_meetings, many=True)
            
              
            data_with_users = []
            
            user_dict={
            "name" : user.firstname+" "+ user.lastname,
            "profile":emp_details.profile_picture
            
            }

            for item in combined_serializer.data:
                

                if 'participant_ids' in item:
                    participant_ids = item['participant_ids']
                    participants = User.objects.filter(id__in=participant_ids).values('id', 'firstname', 'lastname', 'email')
                    item['participant_data'] = list(participants)

                if 'assign_to_ids' in item:
                    assign_to_ids = item['assign_to_ids']
                    assignees = User.objects.filter(id__in=assign_to_ids).values('id', 'firstname', 'lastname', 'email')
                    item['assign_to_data'] = list(assignees)

                data_with_users.append(item)
            
            
            consultationDetails=DoctorConsultation.objects.filter( employee_id = user ).order_by('-appointment_date')
            userSerialData = ShowDoctorConsultationSerializer(consultationDetails, many=True)
            upcoming = json.loads(json.dumps(userSerialData.data))

            response = {
                "success": True,
                "status": 200,
                "message": "Events and meetings and appointments retrieved successfully",
                "data": {
                "user":user_dict,
                "task_nd_meeting":data_with_users,
                "appointments": upcoming
                
                }
            }

            return JsonResponse(response)

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": "User not found"
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": "Failed to retrieve events and meetings",
                "errors": str(e)
            })
            
            
            

    