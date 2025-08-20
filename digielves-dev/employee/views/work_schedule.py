from django.http import JsonResponse
from digielves_setup.models import OrganizationDetails, OrganizationWorkSchedule, User, UserWorkSchedule, UserWorkSlot, Weekday
from organization.seriallizers.work_schedule_seriallizers import OrganizationWorkScheduleSerializer
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
import json
import re
from django.contrib.contenttypes.models import ContentType
class UserWorkScheduleViewSet(viewsets.ModelViewSet):
    
    

    @csrf_exempt
    def add_user_work_schedule(self, request):
        try:
            user_id = request.data.get('user_id')
            slots_str = request.data.get('slots')
            from_date_str = request.data.get('from_date')
            to_date_str = request.data.get('to_date')
            weekdays_str = request.data.get('weekdays')
            working_hours = request.data.get('working_hours')

            if not user_id or not from_date_str or not to_date_str or not weekdays_str or not slots_str:
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
                weekdays = [int(day) for day in weekdays_str.split(',')]
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid date or weekday format'}, status=400)

            user = User.objects.get(pk=user_id)
            SLOT_PATTERN = re.compile(r'^\d{2}:\d{2} - \d{2}:\d{2}$')
            slots = [slot.strip() for slot in slots_str.split(',')]
            valid_slots = set()
            for slot in slots:
                if SLOT_PATTERN.match(slot):
                    valid_slots.add(slot)

            if not valid_slots:
                return JsonResponse({
                    'success': False,
                    'error': 'No valid slots provided'}, status=400)

            current_date = from_date
            created_or_updated_dates = []
            skipped_dates = []

            while current_date <= to_date:
                if current_date.weekday() in weekdays:
                    user_work_schedule, created = UserWorkSchedule.objects.get_or_create(
                        user=user,
                        date=current_date,
                        defaults={'working_hours': working_hours}
                    )

                    # If the schedule already exists and has frozen slots, skip this date
                    if not created and UserWorkSlot.objects.filter(user_work_schedule=user_work_schedule, freeze=True).exists():
                        skipped_dates.append(current_date.strftime('%Y-%m-%d'))
                        current_date += timedelta(days=1)
                        continue

                    # If the schedule already exists, update the working hours
                    if not created:
                        user_work_schedule.working_hours = working_hours
                        user_work_schedule.save()

                    # Delete existing non-frozen slots
                    UserWorkSlot.objects.filter(user_work_schedule=user_work_schedule, freeze=False).delete()

                    # Add new slots
                    for slot in valid_slots:
                        UserWorkSlot.objects.create(
                            user_work_schedule=user_work_schedule,
                            slot=slot,
                        )
                    
                    created_or_updated_dates.append(current_date.strftime('%Y-%m-%d'))

                current_date += timedelta(days=1)

            return JsonResponse({
                'success': True,
                'status': 200,
                'message': f"Work schedule created or updated for dates: {', '.join(created_or_updated_dates)}",
                'skipped_dates': f"Schedules for the following dates were not updated due to frozen slots: {', '.join(skipped_dates)}" if skipped_dates else None
            })

        except User.DoesNotExist:
            return JsonResponse({'error': 'User does not exist'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        

    
    @csrf_exempt
    def get_user_work_schedule(self, request):

        try:
            user_id = request.GET.get('user_id')
            from_date_str = request.GET.get('from_date')
            to_date_str = request.GET.get('to_date')

            if not user_id:
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            user = User.objects.get(pk=user_id)

            # If from_date or to_date is provided, parse them
            if from_date_str:
                try:
                    from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({'error': 'Invalid from_date format'}, status=400)
            else:
                from_date = None

            if to_date_str:
                try:
                    to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({'error': 'Invalid to_date format'}, status=400)
            else:
                to_date = None

            # Retrieve UserWorkSchedule entries based on provided dates
            if from_date and to_date:
                user_work_schedules = UserWorkSchedule.objects.filter(
                    user=user,
                    date__gte=from_date,
                    date__lte=to_date
                ).order_by('date')
            elif from_date:
                user_work_schedules = UserWorkSchedule.objects.filter(
                    user=user,
                    date__gte=from_date
                ).order_by('date')
            elif to_date:
                user_work_schedules = UserWorkSchedule.objects.filter(
                    user=user,
                    date__lte=to_date
                ).order_by('date')
            else:
                user_work_schedules = UserWorkSchedule.objects.filter(
                    user=user
                ).order_by('date')

            if not user_work_schedules.exists():
                return JsonResponse(
                    {'success':True,
                        
                        'work_schedules': []}, status=200)

            # Prepare the response data
            response_data = []
            
            for work_schedule in user_work_schedules:
                slots = UserWorkSlot.objects.filter(user_work_schedule=work_schedule).order_by('slot')
                slot_data = []
                
                for slot in slots:
                    slot_info = {
                        'slot': slot.slot,
                        'freeze': slot.freeze
                    }
                    slot_data.append(slot_info)
                    
                response_data.append({
                        'date': work_schedule.date,
                        'slots': slot_data
                    })

            return JsonResponse(
                {'success':True,
                    
                    'work_schedules': response_data}, status=200)

        except User.DoesNotExist:
            return JsonResponse({'error': 'User does not exist'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


    @csrf_exempt
    def update_user_work_slot(self, request):
        try:
            user_id = request.POST.get('user_id')
            slot_id = request.POST.get('slot_id')
            category = request.POST.get('category')
            object_id = request.POST.get('object_id')

            if not user_id or not slot_id or not category or not object_id:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Invalid request. user_id, slot_id, category, and object_id are required."
                })

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": 404,
                    "message": "User not found."
                })

            try:
                slot = UserWorkSlot.objects.get(id=slot_id, user_work_schedule__user=user)
            except UserWorkSlot.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": 404,
                    "message": "Slot not found."
                })

            try:
                content_type = ContentType.objects.get(model=category.lower())
            except ContentType.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": f"Category '{category}' not found."
                })

            slot.freeze = True
            slot.reschedule = True
            slot.content_type = content_type
            slot.object_id = object_id
            slot.save()

            response = {
                "success": True,
                "status": 200,
                "message": "Slot updated successfully."
            }

            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "errors": str(e)
            })
        

