from django.http import JsonResponse
from digielves_setup.models import OrganizationDetails, OrganizationWorkSchedule, Weekday
from organization.seriallizers.work_schedule_seriallizers import OrganizationWorkScheduleSerializer
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta

class WorkScheduleViewSet(viewsets.ModelViewSet):
    
    

    @csrf_exempt
    def create_schedule(self, request):
        try:
            user_id = request.data.get('user_id')
            start_time = request.data.get('start_time')
            end_time = request.data.get('end_time')
            weekdays = request.data.get('weekdays')
            working_hours = request.data.get('working_hours')
    
            organization = get_object_or_404(OrganizationDetails, user_id=user_id)
          
            #work_schedule = get_object_or_404(OrganizationWorkSchedule, organization=organization)
          

            
            # Validate working hours
            # start_time_obj = datetime.strptime(start_time, '%H:%M:%S').time()
            # end_time_obj = datetime.strptime(end_time, '%H:%M:%S').time()
            # time_difference = (datetime.combine(datetime.min, end_time_obj) - datetime.combine(datetime.min, start_time_obj)).total_seconds() / 3600
            # print(start_time_obj, "    ",end_time_obj )
            # print(time_difference)
            # if time_difference != float(working_hours):
            #     return JsonResponse({
            #         "success": False,
            #         "message": "Start time and end time difference must equal working hours"
            #     }, status=status.HTTP_400_BAD_REQUEST)

            # Check if an OrganizationWorkSchedule already exists
            work_schedule, created = OrganizationWorkSchedule.objects.get_or_create(
            organization=organization,
            defaults={
                'start_time': start_time,
                'end_time': end_time,
                'working_hours': working_hours,
            }
            )
            if not created:
                work_schedule.start_time = start_time
                work_schedule.end_time = end_time
                work_schedule.working_hours = working_hours
                work_schedule.save()
           
            # Delete existing Weekday entries and create new ones
            Weekday.objects.filter(organizationworkschedule=work_schedule).delete()
          
            weekdays_list = weekdays.split(',')
            for day in weekdays_list:
                Weekday.objects.create(
                    organizationworkschedule=work_schedule,
                    name=day.strip()
                )

            message = "Work schedule created successfully" if created else "Work schedule updated successfully"
            return JsonResponse({
                "success": True,
                "message": message
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

        except OrganizationDetails.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "Organization not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": "Internal server error",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @csrf_exempt
    def get_schedule(self, request):
        user_id = request.GET.get('user_id')
        
        try:
            organization = get_object_or_404(OrganizationDetails, user_id=user_id)
            work_schedules = OrganizationWorkSchedule.objects.filter(organization=organization)
            
            if not work_schedules.exists():
                return JsonResponse({
                    "success": False,
                    "message": "No work schedules found for this organization"
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = OrganizationWorkScheduleSerializer(work_schedules, many=True)
            return JsonResponse({
                "success": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        except OrganizationDetails.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "Organization not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": "Internal server error",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
