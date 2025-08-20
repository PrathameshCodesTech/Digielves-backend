
from digielves_setup.models import DoctorConsultation, DoctorLeaves, DoctorPersonalDetails, DoctorSlot, Notification, OrganizationBranch, OrganizationDetails, EmployeePersonalDetails, Redirect_to, User
from doctor.seriallizers.doctor_slot_seriallizer import DoctorSlotSerializer, GetDoctorSlotSerializer
from organization.seriallizers.organization_branch_seriallizer import OrganizationDetailsSerializer
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import status
# from datetime import 
from datetime import datetime
from datetime import date as for_today
import json
from collections import defaultdict
from datetime import timedelta, date
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
class DoctorSlotViewSet(viewsets.ModelViewSet):

    serializer_class = DoctorSlotSerializer
    
    

    
    # @csrf_exempt
    # def AddSlots(self, request):
    #     print(request.data)
    #     try:
    #         slots_data = json.loads(request.data.get('slots'))
    #         doctor_pk = request.data.get('doctor') 
    #         doctor = DoctorPersonalDetails.objects.filter(user_id_id=doctor_pk).first()
    #         print(doctor)
    #         if not slots_data or not isinstance(slots_data, list):
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": status.HTTP_400_BAD_REQUEST,
    #                 "message": "Invalid request. 'slots' must be a list of strings representing slots."
    #             })
    #         date = request.data.get('date')
    #         existing_slots = DoctorSlot.objects.filter(doctor=doctor.pk, date=date)
    #         if existing_slots.exists():
    #             return JsonResponse({
    #                 "success": True,
    #                 "date":True,
    #                 "status": status.HTTP_400_BAD_REQUEST,
    #                 "message": f"Slots for the date {date} already exist."

    #             })



    #         slots_created = []
    #         for slot in slots_data:
    #             print(slot)
    #             slot_entry = {
    #                 "doctor": doctor.pk,                   
    #                 "organization": request.data.get('organization'),
    #                 "meeting_mode": request.data.get('meeting_mode'),
    #                 "date":request.data.get('date'),
    #                 "slots": slot 
    #             }

    #             organization_branch = request.data.get('organization_branch')
    #             if request.data.get('meeting_mode')=="Online" or organization_branch == 'null':
    #                 slot_entry['organization_branch'] = None
    #             elif organization_branch is not None:
    #                 slot_entry['organization_branch'] = organization_branch

    #             serializer = DoctorSlotSerializer(data=slot_entry)
    #             if serializer.is_valid():
    #                 doctor_slot = serializer.save()
    #                 slots_created.append(serializer.data)
    #             else:
    #                 return JsonResponse({
    #                     "success": False,
    #                     "status": status.HTTP_400_BAD_REQUEST,
    #                     "message": "Failed to create Slot.",
    #                     "errors": serializer.errors
    #                 })

    #         return JsonResponse({
    #             "success": True,
    #             "status": status.HTTP_201_CREATED,
    #             "message": "Slots created successfully.",
    #             "data": slots_created
    #         })

    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "Internal server error.",
    #             "errors": str(e)
    #         })
            
            
    def calculate_remaining_weekdays(self, from_date, to_date, included_weekdays):
        current_date = from_date
        remaining_weekdays = []

        while current_date <= to_date:
            if current_date.weekday() in included_weekdays:
                remaining_weekdays.append(str(current_date))
            current_date += timedelta(days=1)

        return remaining_weekdays
    
    @csrf_exempt
    def AddSlot(self, request):
        print(request.data)
        try:
            doctor_pk = request.data.get('doctor') 
            user_id = request.data.get('user_id') 
            from_date_str = request.data.get('from_date')
            to_date_str = request.data.get('to_date')
   
            included_weekdays_str = request.data.get('included_weekdays', '')
        
            slots_data = json.loads(request.data.get('slots'))
            
            
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            doctor = DoctorPersonalDetails.objects.filter(user_id_id=doctor_pk).first()
            
            included_weekdays = [int(day) for day in included_weekdays_str.split(',') if day]
            
            if not included_weekdays:
               
                included_weekdays = [0, 1, 2, 3, 4, 5, 6] 

            
            if from_date > to_date:
                return JsonResponse({"error": "from_date should be before to_date"}, status=400)
          
            remaining_weekdays = self.calculate_remaining_weekdays(from_date, to_date, included_weekdays)
            
            try:
                
                slots_created = []
                
                existing_dates = []
                
                
                for remaining_date_str in remaining_weekdays:
                    
                    
                
                    remaining_date = datetime.strptime(remaining_date_str, '%Y-%m-%d').date()
                    
                    existing_date = DoctorSlot.objects.filter(doctor=doctor, date=remaining_date).first()
                    
                    if existing_date:
                        
                        existing_dates.append(str(existing_date.date))
                        
                        continue
                    
                    existing_leave = DoctorLeaves.objects.filter(doctor=doctor, date=remaining_date).first()
                    if existing_leave:
                        existing_leave.delete()
                    
                    doctor_leave = DoctorLeaves.objects.create(doctor=doctor, date=remaining_date)
                    for slot in slots_data:
                        
                        slot_entry = {
                            "doctor": doctor.pk,                   
                            "organization": request.data.get('organization'),
                            "meeting_mode": request.data.get('meeting_mode'),
                            "date": remaining_date,
                            "slots": slot 
                        }

                        organization_branch = request.data.get('organization_branch')
                        if request.data.get('meeting_mode') == "Online" or organization_branch == 'null':
                            slot_entry['organization_branch'] = None
                        elif organization_branch is not None:
                            slot_entry['organization_branch'] = organization_branch

                        serializer = DoctorSlotSerializer(data=slot_entry)
                        if serializer.is_valid():
                            doctor_slot = serializer.save()
                            slots_created.append(serializer.data)
                        else:
                            return JsonResponse({
                                "success": False,
                                "status": status.HTTP_400_BAD_REQUEST,
                                "message": "Failed to create Slot.",
                                "errors": serializer.errors
                            })
                
                
                response_data = {
                        "success": True,
                        "status": status.HTTP_201_CREATED,
                        "message": "Slots created successfully.",
                        
                    }         
                if existing_dates:
                    
                    response_data["message"] += f" Some slots already exist on the following dates: {', '.join(existing_dates)}."
                            
                return JsonResponse(response_data)
            except Exception as e:
                return JsonResponse({
                    "success": False,
                    "status": 500,
                    "message": "Internal server error.",
                    "errors": str(e)
                })

                    

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": "Internal server error.",
                "errors": str(e)
            })
            
            
            
    
    @csrf_exempt
    def UpdateLeave(self, request):
        try:
            with transaction.atomic():
                user_id = request.data.get('user_id')
                date_str = request.data.get('date')
                if not (user_id and date_str):
                    return JsonResponse({
                        "success": False,
                        "status": 400,
                        "message": "Invalid request. user_id and date are required."
                    })

                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                doctor = DoctorPersonalDetails.objects.filter(user_id=user_id).first()

                if not doctor:
                    return JsonResponse({
                        "success": False,
                        "status": 404,
                        "message": f"Doctor with user_id {user_id} not found."
                    })
                print("-----------------------hmm1")
                slots_to_delete = DoctorSlot.objects.filter(doctor=doctor, date=date)
                freeze_slots = DoctorSlot.objects.filter(doctor=doctor, date=date, freeze=True)
                user = User.objects.get(id=user_id)
                for freeze_slot in freeze_slots:
                    try:
                        
                        consultation=DoctorConsultation.objects.get(doctor_slot=freeze_slot)
                        consultation.status = "Cancelled"
                        consultation.save()
                        
                        notification = Notification.objects.create(
                            user_id=user,
                            where_to="doctorcunsultation",
                            notification_msg="Consultation cancelled by doctor",
                            action_content_type=ContentType.objects.get_for_model(DoctorConsultation),
                            action_id=consultation.id
                        )

                        notification.notification_to.set([consultation.employee_id.id])
                        Redirect_to.objects.create(notification=notification, link="/employee/doctorConsultation")
                    except DoctorConsultation.DoesNotExist:
                        print(f"No consultation found for frozen slot with ID {freeze_slot.id}")

                deleted_count,_ = slots_to_delete.delete()

                # You can also delete the date itself if no slots remain for that date
                if not DoctorSlot.objects.filter(date=date).exists():
                    DoctorSlot.objects.filter(date=date).delete()

                doctor_leave, created = DoctorLeaves.objects.get_or_create(doctor=doctor, date=date)
                
                doctor_leave.on_leave = True
                doctor_leave.save()

                return JsonResponse({
                    "success": True,
                    "status": 200,
                    "message": f"Cancelled {deleted_count} slots for user {user_id} on {date_str}."
                })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": 404,
                "message": f"User with ID {user_id} not found."
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": "Failed to cancel slots.",
                "errors": str(e)
            })
            
            



    @csrf_exempt
    def GetSlots(self,request):
        try:
            user_id = request.GET.get("user_id")
            organization_branch_id = request.GET.get('organization_branch_id')
            organization_id = request.GET.get('organization_id')
            doctor_id = request.GET.get('doctor_id')
            date = request.GET.get('date')
            meet_mode=request.GET.get('metting_mode')
            

            doctor = DoctorPersonalDetails.objects.filter(user_id=doctor_id).first()
            if not doctor:
                return JsonResponse({
                    "success": False,
                    "status": 404,
                    "message": "Doctor not found for the given user_id."
                })

            if  not organization_id or not doctor or not date:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request.organization_id, doctor_id and date are required."
                })
            
            user = User.objects.get(id=user_id)
            
            emp_details=EmployeePersonalDetails.objects.get(user_id=user.id)
            print(emp_details.organization_id)
            
            
            current_datetime = datetime.now()  # Get the current date and time
            current_date = current_datetime.date()
            current_time = current_datetime.time()
            formatted_current_time = f"{current_time.hour:02d}:{current_time.minute:02d}"

            
            if meet_mode=="Online":
                slots = DoctorSlot.objects.filter(
    
                    organization_id=emp_details.organization_id,
                    doctor_id=doctor,
                    freeze=False,
                    date=date,
                    
                ).exclude(date=current_date, slots__lt=f"{formatted_current_time}:")
            else:
                slots = DoctorSlot.objects.filter(
    
                    organization_id=emp_details.organization_id,
                    doctor_id=doctor,
                    freeze=False,
                    date=date,
                    meeting_mode=meet_mode if meet_mode=="Offline" else "Online"
                ).exclude(date=current_date, slots__lt=f"{formatted_current_time}:")
                
            
            
            
            if organization_branch_id:
                slots = slots.filter(organization_branch_id=organization_branch_id)

            

            serializer = GetDoctorSlotSerializer(slots, many=True)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Slots retrieved successfully.",
                "data": serializer.data
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve slots.",
                "errors": str(e)
            })
        

    @csrf_exempt
    def UpdateSlotFreeze(self,request):
        try:
            user_id = request.data.get('user_id')
            slot_id = request.data.get('slot_id')

            if not user_id or not slot_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. Both user_id and slot_id are required."
                })

            slot = DoctorSlot.objects.filter(id=slot_id).first()
            if not slot:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Slot not found."
                })

            

            slot.freeze = True
            slot.save()

            serializer = DoctorSlotSerializer(slot)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Slot freeze status updated successfully.",
                "data": serializer.data
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update slot freeze status.",
                "errors": str(e)
            })
        
    
    @csrf_exempt
    def get_today_slots(self, request):

        try:
            user_id = request.GET.get('user_id')
            from_date = request.GET.get('from_date')
            to_date = request.GET.get('to_date')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Invalid request. user_id is required."
                })

            doctor = DoctorPersonalDetails.objects.filter(user_id=user_id).first()
            if not doctor:
                return JsonResponse({
                    "success": False,
                    "status": 404,
                    "message": "Doctor not found for the given user_id."
                })
            
            

            if from_date and to_date:
                try:
                    from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                    to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        from_date = datetime.strptime(from_date, '%Y/%m/%d').date()
                        to_date = datetime.strptime(to_date, '%Y/%m/%d').date()
                    except ValueError:
                        return JsonResponse({
                            "success": False,
                            "status": 400,
                            "message": "Invalid date format. Dates should be in the format 'YYYY-MM-DD' or 'YYYY/MM/DD'."
                        })

                slots = DoctorSlot.objects.filter(doctor=doctor, date__range=[from_date, to_date])
            else:
                # today = timezone.now().date()
                today = for_today.today()
                slots = DoctorSlot.objects.filter(doctor=doctor, date=today)

            grouped_slots = defaultdict(lambda: defaultdict(list))
            for slot in slots:
                grouped_slots[slot.date][slot.organization_branch_id].append({
                    "id": slot.id,
                    "slots": slot.slots,
                    "freeze": slot.freeze,
                    "meeting_mode": slot.meeting_mode,
                    "created_at": slot.created_at,
                    "updated_at": slot.updated_at,
                    "organization": slot.organization_id
                })

            result = {"uniq": []}
            for date, branch_slots in grouped_slots.items():
                

                for branch_id, slots_data in branch_slots.items():
                    branch = None 
                    if branch_id:
                        branch = OrganizationBranch.objects.filter(id=branch_id).first()
                        if not branch:
                            continue
                    
                    result_data = []
                    freeze_count = 0  
                    for slot_data in slots_data:
                        organization_id = slot_data.get("organization")  
                        
                        organization = None
                        if organization_id:
                            organization = OrganizationDetails.objects.filter(id=organization_id).first()
                        
                        organization_data = {
                            "id": organization.id if organization else None,
                            "name": organization.name if organization else None,
                            "support_mail": organization.support_mail if organization else None,
                            # Add other fields you want to include
                        }
                        
                        if slot_data["freeze"] == "True":
                            freeze_count += 1
                        
                        result_data.append({
                            "id": slot_data["id"],
                            "slots": slot_data["slots"],
                            "freeze": slot_data["freeze"],
                            "meeting_mode": slot_data["meeting_mode"],
                            "created_at": slot_data["created_at"],
                            "updated_at": slot_data["updated_at"],
                            "organization": organization_data
                        })
                    
                    branch_data = {
                        "id": branch.id if branch else None,
                        "name": branch.branch_name if branch else None,
                        "organization": None
                    }
                    
                    result["uniq"].append({
                        "organization_branch": branch_data,
                        "meeting_mode": slots_data[0]["meeting_mode"],
                        "date": date,
                        "slots": result_data,
                        "freeze_count": freeze_count 
                    })

            return JsonResponse({
                "success": True,
                "status": 200,
                "message": "Slots retrieved successfully.",
                "data": result["uniq"]
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": "Failed to retrieve slots.",
                "errors": str(e)
            })
            

    @csrf_exempt
    def delete_slots(self, request):
        try:
            user_id = request.GET.get('user_id')
            date_str = request.GET.get('date')
            if not (user_id and date_str):
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Invalid request. user_id and date are required."
                })
            
            # Convert date_str to a datetime object
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            doctor = DoctorPersonalDetails.objects.filter(user_id=user_id).first()
        
        # Filter slots for the given user and date, and then delete all matching rows
            deleted_count, _ = DoctorSlot.objects.filter(doctor=doctor, date=date).delete()
            
            # You can also delete the date itself if no slots remain for that date
            if DoctorSlot.objects.filter(date=date).count() == 0:
                DoctorSlot.objects.filter(date=date).delete()
        
            doctor_leave = DoctorLeaves.objects.filter(doctor=doctor, date=date).last().delete()
            return JsonResponse({
                "success": True,
                "status": 200,
                "message": f"Deleted {deleted_count} slots for user {user_id} on {date_str}."
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": "Failed to delete slots.",
                "errors": str(e)
            })
    

#    @csrf_exempt
#    def delete_slots(self, request):
#        try:
#            user_id=request.GET.get('user_id')
#            date_str = request.GET.get('date')
#            if not (user_id and date_str):
#                return JsonResponse({
#                    "success": False,
#                    "status": 400,
#                    "message": "Invalid request. user_id and date is required."
#                })
#            # doctor = DoctorPersonalDetails.objects.filter(user_id=user_id).first()
#            date = datetime.strptime(date_str, '%Y-%m-%d').date()
#            
#            print(user_id)
#            print(date)
#            deleted_count, _ = DoctorSlot.objects.filter(doctor=user_id, date=date).delete()
#            return JsonResponse({
#                "success": True,
#                "status": 200,
#                "message": f"Deleted {deleted_count} slots for user {user_id} on {date_str}."
#            })
#        except Exception as e:
#            return JsonResponse({
#                "success": False,
#                "status": 500,
#                "message": "Failed to delete slots.",
#                "errors": str(e)
#            })

    # @csrf_exempt
    # def get_today_slots(self, request):

    #     try:
    #         user_id = request.GET.get('user_id')
    #         from_date = request.GET.get('from_date')
    #         to_date = request.GET.get('to_date')

    #         if not user_id:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": 400,
    #                 "message": "Invalid request. user_id is required."
    #             })

    #         doctor = DoctorPersonalDetails.objects.filter(user_id=user_id).first()
    #         if not doctor:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": 404,
    #                 "message": "Doctor not found for the given user_id."
    #             })

    #         if from_date and to_date:
    #             try:
    #                 from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
    #                 to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
    #             except ValueError:
    #                 try:
    #                     from_date = datetime.strptime(from_date, '%Y/%m/%d').date()
    #                     to_date = datetime.strptime(to_date, '%Y/%m/%d').date()
    #                 except ValueError:
    #                     return JsonResponse({
    #                         "success": False,
    #                         "status": 400,
    #                         "message": "Invalid date format. Dates should be in the format 'YYYY-MM-DD' or 'YYYY/MM/DD'."
    #                     })

    #             slots = DoctorSlot.objects.filter(doctor=doctor, date__range=[from_date, to_date])
    #         else:
    #             # today = timezone.now().date()
    #             today = for_today.today()
    #             slots = DoctorSlot.objects.filter(doctor=doctor, date=today)

    #         grouped_slots = defaultdict(lambda: defaultdict(list))
    #         for slot in slots:
    #             grouped_slots[slot.date][slot.organization_branch_id].append({
    #                 "id": slot.id,
    #                 "slots": slot.slots,
    #                 "freeze": slot.freeze,
    #                 "meeting_mode": slot.meeting_mode,
    #                 "created_at": slot.created_at,
    #                 "updated_at": slot.updated_at,
    #                 "organization": slot.organization_id
    #             })

    #         result = {"uniq": []}
    #         for date, branch_slots in grouped_slots.items():
    #             for branch_id, slots_data in branch_slots.items():
    #                 branch = None 
    #                 if branch_id:
    #                     branch = OrganizationBranch.objects.filter(id=branch_id).first()
    #                     if not branch:
    #                         continue

    #                 branch_data = {
    #                     "id": branch.id if branch else None,
    #                     "name": branch.branch_name if branch else None,
    #                 }
                    
    #                 organization = branch.org if branch else None
    #                 organization_serializer = OrganizationDetailsSerializer(organization)

    #                 result["uniq"].append({
    #                     "organization_branch": branch_data,
    #                     "organization": organization_serializer.data,
    #                     "meeting_mode": slots_data[0]["meeting_mode"], 
    #                     "date": date,
    #                     "slots": slots_data
    #                 })
    #         return JsonResponse({
    #             "success": True,
    #             "status": 200,
    #             "message": "Slots retrieved successfully.",
    #             "data": result["uniq"]
    #         })

    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": 500,
    #             "message": "Failed to retrieve slots.",
    #             "errors": str(e)
    #         })
        
    
    # @csrf_exempt
    # def update_slots_and_consultations(self, request):
    #     try:
    #         user_id = request.data.get('user_id')
    #         date = request.data.get('date')
    #         meeting_mode = request.data.get('meeting_mode')
    #         organization_id = request.data.get('organization_id')
    #         organization_branch_id = request.data.get('organization_branch_id')
    #         slots_data = json.loads(request.data.get('slots'))


    #         if not slots_data or not isinstance(slots_data, list):
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": status.HTTP_400_BAD_REQUEST,
    #                 "message": "Invalid request. 'slots' must be a list of strings representing slots."
    #             })

    #         # Scenario 1: Change meeting_mode from Online to Offline
    #         doctor = DoctorPersonalDetails.objects.filter(user_id=user_id).first()
    #         existing_slots = DoctorSlot.objects.filter(doctor=doctor, date=date)
    #         has_online_slots = DoctorSlot.objects.filter(doctor=doctor, date=date, meeting_mode="Online").exists()
    #         if has_online_slots and meeting_mode == "Offline":
    #             doctor_slots = DoctorSlot.objects.filter(doctor=doctor, date=date)
    #             for slot in doctor_slots:
    #                 slot.meeting_mode = meeting_mode
    #                 slot.save()

    #         # Scenario 2: Change meeting_mode from Offline to Online if same prev org_id and org_branch_id
    #         elif DoctorSlot.objects.filter(doctor=doctor, date=date, meeting_mode="Offline").exists():
    #             if meeting_mode == "Online":
    #                 if DoctorSlot.objects.filter(doctor=doctor, date=date, organization_id=organization_id, organization_branch=organization_branch_id).exists():
    #                     doctor_slots = DoctorSlot.objects.filter(doctor=doctor, date=date)
    #                     for slot in doctor_slots:
    #                         slot.meeting_mode = meeting_mode
    #                         slot.save()
    #                         DoctorConsultation.objects.filter(doctor_slot=slot, meeting_pref_type="Offline").update(status="Cancelled")
    #                 elif DoctorSlot.objects.filter(doctor=doctor, date=date, organization_id=organization_id).exists():
    #                     doctor_slots = DoctorSlot.objects.filter(doctor=doctor, date=date)
    #                     for slot in doctor_slots:
    #                         slot.meeting_mode = meeting_mode
    #                         slot.save()
    #                         DoctorConsultation.objects.filter(doctor_slot=slot, meeting_pref_type="Offline").update(status="Cancelled")
    #                 else:
    #                     doctor_slots = DoctorSlot.objects.filter(doctor=doctor, date=date)
    #                     for slot in doctor_slots:
    #                         slot.meeting_mode = meeting_mode
    #                         slot.save()
    #                         DoctorConsultation.objects.filter(doctor_slot=slot).update(status="Cancelled")
            
            
    #         return JsonResponse({
    #             "success": True,
    #             "status": status.HTTP_200_OK,
    #             "message": "Slots and consultations updated successfully."
    #         })

    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "Failed to update slots and consultations.",
    #             "errors": str(e)
    #         })



    @csrf_exempt
    def update_slots_and_consultations(self, request):
        try:
            user_id = request.data.get('user_id')
            date = request.data.get('date')
            
            meeting_mode = request.data.get('meeting_mode')
            organization_id = request.data.get('organization_id')
            organization_branch_id = request.data.get('organization_branch_id')
            
            # slots_data = json.loads(request.data.get('slots'))

            # Scenario 1: Change meeting_mode from Online to Offline
            print(user_id)
            doctor_slotss = DoctorPersonalDetails.objects.filter(user_id_id=user_id).first()
            print("----soctore")
            print(doctor_slotss)
            print(date)
            has_online_slots = DoctorSlot.objects.filter(doctor=doctor_slotss, date=date, meeting_mode="Online").exists()
            print(has_online_slots)
            if has_online_slots:
                print("------hey")
                if meeting_mode == "Offline":
                    
                    doctor_slots = DoctorSlot.objects.filter(doctor=doctor_slotss, date=date)
                    print(doctor_slots)
                    for slot in doctor_slots:
                        slot.meeting_mode = meeting_mode
                        slot.save()

            # Scenario 2: Change meeting_mode from Offline to Online if same prev org_id and org_branch_id
            elif DoctorSlot.objects.filter(doctor=doctor_slotss, date=date, meeting_mode="Offline").exists():
                print("yess elif")
                if meeting_mode == "Online":
                    
                    if DoctorSlot.objects.filter(doctor=doctor_slotss,date=date,organization_id=organization_id,organization_branch=organization_branch_id).exists():

                        print("----nooooo")
                        doctor_slots = DoctorSlot.objects.filter(doctor=doctor_slotss, date=date)
                        print(doctor_slots)
                        for slot in doctor_slots:
                            
                            print(slot)
                            
                            slot.meeting_mode = meeting_mode            
                            slot.save()
                            DoctorConsultation.objects.filter(doctor_slot=slot, meeting_pref_type="Offline").update(status="Cancelled")
                    elif DoctorSlot.objects.filter(doctor=doctor_slotss,date=date,organization_id=organization_id).exists():
                        print("-----jjjj")
                        doctor_slots = DoctorSlot.objects.filter(doctor=doctor_slotss, date=date)
                        print(doctor_slots)
                        for slot in doctor_slots:
                            
                            print(slot)
                            
                            slot.meeting_mode = meeting_mode            
                            slot.save()
                            DoctorConsultation.objects.filter(doctor_slot=slot, meeting_pref_type="Offline").update(status="Cancelled")
                    else:
                        doctor_slots = DoctorSlot.objects.filter(doctor=doctor_slotss, date=date)
                        print(doctor_slots)
                        for slot in doctor_slots:
                            
                            print(slot)
                            
                            slot.meeting_mode = meeting_mode            
                            slot.save()
                            DoctorConsultation.objects.filter(doctor_slot=slot).update(status="Cancelled")
            doctor_slotss = DoctorPersonalDetails.objects.filter(user_id=user_id).first()
            print(date)
            print("------krke")
            print(doctor_slotss)
            scheduled_slots = []
            slots = DoctorSlot.objects.filter(doctor=doctor_slotss, date=date).values_list('slots')
            print("-----ganapati baappa")
            print(slots)
            for slot in slots:
                scheduled_slots.append(slot[0])
            print("from DB")

            print(scheduled_slots)
            
            updated_slots = json.loads(request.data.get('slots'))
            for slot in scheduled_slots:
                if slot not in updated_slots:

                    DoctorSlot.objects.filter(doctor=doctor_slotss, date=date, slots = slot ).delete()
            
            for slot in updated_slots:
                print(f"s-------{slot}")
                if slot not in scheduled_slots:
                    
                    print(slot)
                    print(doctor_slotss.pk)
                    slot_entry = {
                        "doctor": doctor_slotss.pk,                   
                        "organization": request.data.get('organization_id'),
                        "meeting_mode": request.data.get('meeting_mode'),
                        "date":request.data.get('date'),
                        "slots": slot 
                    }

                    organization_branch = request.data.get('organization_branch_id')
                    if organization_branch == 'null':
                        slot_entry['organization_branch'] = None
                    elif organization_branch is not None:
                        slot_entry['organization_branch'] = organization_branch

                    serializer = DoctorSlotSerializer(data=slot_entry)
                    if serializer.is_valid():
                        doctor_slot = serializer.save()
                    else:
                        return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Failed to create Slot.",
                            "errors": serializer.errors
                        })


            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Slots and consultations updated successfully."
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update slots and consultations.",
                "errors": str(e)
            })


# 7 aug

    # @csrf_exempt
    # def get_today_slots(self, request):

    #     try:
    #         user_id = request.GET.get('user_id')
    #         from_date = request.GET.get('from_date')
    #         to_date = request.GET.get('to_date')

    #         if not user_id:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": 400,
    #                 "message": "Invalid request. user_id is required."
    #             })

    #         doctor = DoctorPersonalDetails.objects.filter(user_id=user_id).first()
    #         if not doctor:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": 404,
    #                 "message": "Doctor not found for the given user_id."
    #             })
            

    #         if from_date and to_date:
    #             try:
    #                 from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
    #                 to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
    #             except ValueError:
    #                 try:
    #                     from_date = datetime.strptime(from_date, '%Y/%m/%d').date()
    #                     to_date = datetime.strptime(to_date, '%Y/%m/%d').date()
    #                 except ValueError:
    #                     return JsonResponse({
    #                         "success": False,
    #                         "status": 400,
    #                         "message": "Invalid date format. Dates should be in the format 'YYYY-MM-DD' or 'YYYY/MM/DD'."
    #                     })


    #             slots = DoctorSlot.objects.filter(doctor=doctor, date__range=[from_date, to_date])
    #         else:
    #             print("----------------------------")
    #             today = for_today.today()
    #             slots = DoctorSlot.objects.filter(doctor=doctor, date=today)
    #             serializer = DoctorSlotSerializer(slots, many=True)
                

    #             return JsonResponse({
    #                 "success": True,
    #                 "status": 200,
    #                 "message": "Slots retrieved successfully.",
    #                 "data": {
    #                     "slots":serializer.data
    #                 }
    #             })

            
    #         grouped_slots = defaultdict(lambda: defaultdict(list))
    #         for slot in slots:
    #             grouped_slots[slot.date][slot.organization_branch_id].append({
    #                 "id": slot.id,
    #                 "slots": slot.slots,
    #                 "freeze": slot.freeze,
    #                 "meeting_mode": slot.meeting_mode,
    #                 "created_at": slot.created_at,
    #                 "updated_at": slot.updated_at,
    #                 "organization": slot.organization_id
    #             })

            
    #         result = {"uniq": []}
    #         for date, branch_slots in grouped_slots.items():
    #             for branch_id, slots_data in branch_slots.items():
    #                 branch = OrganizationBranch.objects.filter(id=branch_id).first()
    #                 if not branch:
    #                     continue

    #                 organization = branch.org
    #                 if not organization:
    #                     continue

    #                 branch_data = {
    #                     "id": branch.id,
    #                     "name": branch.branch_name,
                        
    #                 }  
    #                 organization_serializer = OrganizationDetailsSerializer(organization)

    #                 result["uniq"].append({
    #                     "organization_branch": branch_data,
    #                     "organization": organization_serializer.data,
    #                     "date": date,
    #                     "slots": slots_data
    #                 })

    #         return JsonResponse({
    #             "success": True,
    #             "status": 200,
    #             "message": "Slots retrieved successfully.",
    #             "data": result["uniq"]
    #         })

    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": 500,
    #             "message": "Failed to retrieve slots.",
    #             "errors": str(e)
    #         })





        # try:
        #     user_id = request.GET.get('user_id')
        #     from_date = request.GET.get('from_date')
        #     to_date = request.GET.get('to_date')

        #     if not user_id:
        #         return JsonResponse({
        #             "success": False,
        #             "status": 400,
        #             "message": "Invalid request. user_id is required."
        #         })

        #     doctor = DoctorPersonalDetails.objects.filter(user_id=user_id).first()
        #     if not doctor:
        #         return JsonResponse({
        #             "success": False,
        #             "status": 404,
        #             "message": "Doctor not found for the given user_id."
        #         })

        #     if from_date and to_date:
        #         try:
        #             from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        #             to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
        #         except ValueError:
        #             from_date = datetime.strptime(from_date, '%Y/%m/%d').date()
        #             to_date = datetime.strptime(to_date, '%Y/%m/%d').date()

        #         slots = DoctorSlot.objects.filter(doctor=doctor, date__range=[from_date, to_date])
        #     else:
        #         today = date.today()
        #         slots = DoctorSlot.objects.filter(doctor=doctor, date=today)

        #     serializer = DoctorSlotSerializer(slots, many=True)

        #     return JsonResponse({
        #         "success": True,
        #         "status": 200,
        #         "message": "Slots retrieved successfully.",
        #         "data": serializer.data
        #     })

        # except Exception as e:
        #     return JsonResponse({
        #         "success": False,
        #         "status": 500,
        #         "message": "Failed to retrieve slots.",
        #         "errors": str(e)
        #     })

    # @csrf_exempt
    # def get_today_slots(self,request):
    #     try:
    #         user_id = request.GET.get('user_id')

    #         if not user_id:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": 400,
    #                 "message": "Invalid request. user_id is required."
    #             })

    #         doctor = DoctorPersonalDetails.objects.filter(user_id=user_id).first()
    #         if not doctor:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": 404,
    #                 "message": "Doctor not found for the given user_id."
    #             })

    #         today = date.today()

    #         slots = DoctorSlot.objects.filter(doctor=doctor, date=today)
    #         serializer = DoctorSlotSerializer(slots, many=True)

    #         return JsonResponse({
    #             "success": True,
    #             "status": 200,
    #             "message": "Today's slots retrieved successfully.",
    #             "data": serializer.data
    #         })

    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": 500,
    #             "message": "Failed to retrieve today's slots.",
    #             "errors": str(e)
    #         })
        
    # @csrf_exempt
    # def get_today_slots(self,request):
    #     try:
    #         doctor_id = request.GET.get('doctor_id')

    #         if not doctor_id:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": 400,
    #                 "message": "Invalid request. doctor_id is required."
    #             })

    #         today = date.today()

    #         slots = DoctorSlot.objects.filter(doctor_id=doctor_id, date=today)
    #         serializer = DoctorSlotSerializer(slots, many=True)

    #         return JsonResponse({
    #             "success": True,
    #             "status": 200,
    #             "message": "Today's slots retrieved successfully.",
    #             "data": serializer.data
    #         })

    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": 500,
    #             "message": "Failed to retrieve today's slots.",
    #             "errors": str(e)
    #         })