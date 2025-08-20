import base64
import json
import os
import random
from django.shortcuts import render
from configuration.authentication import JWTAuthenticationUser
from configuration.generateGoogleMeet import generateMeeting
from configuration.gzipCompression import compress
from digielves_setup.models import ConsultationReport, DoctorSlot, EmployeeCancelConsultationLimit, OrganizationBranch, User, DoctorConsultation, DoctorConsultationDetails, DoctorPersonalDetails, EmployeePersonalDetails, Notification, Redirect_to
from digielves_setup.validations import is_valid_image
from doctor.seriallizers.doctor_serillizer import DoctorPersonalDetailsSerializer, ShowDoctorPersonalDetailsSerializer
from employee.seriallizers.doctor_consultation_serializer import DoctorConsultationDetailsForFilterSerializer, DoctorConsultationDetailsInOneSerializer, DoctorConsultationDetailsSerializer, DoctorConsultationFilterSerializer, ShowDoctorConsultationSerializer ,DoctorConsultationSerializer, RescheduleConsultaionSerializer, ShowDoctorConsultationDetailsSerializer, ShowDoctorConsultationSerializer, UpdateDoctorConsultationSerializer


from rest_framework import viewsets
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from django.db.models import Count
from django.db.models.functions import Length

from rest_framework import status
from django.shortcuts import get_object_or_404

# Authentication Modules for rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.permissions import  IsAuthenticated ,AllowAny
from django.db.models import Q
from django.db.models import Max

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from employee.seriallizers.personal_details_seriallizer import EmployeePersonalDetailsSerializer, EmployeePersonalDetailsConsultationSerializer
from datetime import date


from celery import shared_task
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from transformers import pipeline
#from PyPDF2 import PdfFileReader
from PyPDF2 import PdfReader
import threading
from django.contrib.contenttypes.models import ContentType

from configuration.zoomMeeting import create_zoom_meeting

from django.http import HttpResponse
from reportlab.pdfgen import canvas
from io import BytesIO
from rest_framework.response import Response
import PyPDF2

class ConsultationDetailsClass(viewsets.ModelViewSet):

    authentication_classes = [JWTAuthenticationUser]
    permission_classes = [IsAuthenticated ]
    # permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle,UserRateThrottle]

    # Client Registration API 
    serializer_class = DoctorConsultationDetailsSerializer
    @csrf_exempt
    def AddConsultationDetails(self,request):
        print(request.data)                                                                                                                                                                                                        
        consultationDetails=DoctorConsultationDetails()
        try:
            userSerialData = self.serializer_class(consultationDetails,data=request.data)
            try:
                if userSerialData.is_valid(raise_exception=True):
                    userSerialData.save()

                    

                    return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": " Consultation Details Added successfully",
                    'data':
                        {
                            'consultation_details_id': consultationDetails.id
                        }
                    })        
            except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Add Consultation Details",
                        "errors": str(e)
                        })
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Add Consultation Details",
                        "errors": str(e)
                        })


    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('user_id', openapi.IN_QUERY, description="Parameter User ID", type=openapi.TYPE_INTEGER,default=2),
    openapi.Parameter('relation', openapi.IN_QUERY, description="Appointment for", type=openapi.TYPE_STRING,default="Self")

    ]) 
    @csrf_exempt
    def GetConsultationDetails(self,request):
        print(request.GET)                                                                                                                                                                                                        
        try:
            addNew = False
            print(request.GET.get('relation') )
        
            consultationDetails=EmployeePersonalDetails.objects.filter(user_id = request.GET.get('user_id'))
            userSerialData = EmployeePersonalDetailsConsultationSerializer(consultationDetails, many=True)
            print(userSerialData)

            personal_details = json.loads(json.dumps(userSerialData.data))
                    
            print("others")
            consultationDetails=DoctorConsultationDetails.objects.filter(employee_id = request.GET.get('user_id')).exclude( relationship =  "Self")
            userSerialData = ShowDoctorConsultationDetailsSerializer(consultationDetails, many=True)
            all_details = json.loads(json.dumps(userSerialData.data))
            
            
            consultationDetailsSelf=DoctorConsultationDetails.objects.filter(employee_id = request.GET.get('user_id'),  relationship =  "Self")
            userSerialData = ShowDoctorConsultationDetailsSerializer(consultationDetailsSelf, many=True)
            all_details_self = json.loads(json.dumps(userSerialData.data))

            response={
                 "success": True,
            "status": status.HTTP_201_CREATED,                
            "message": " Consultation Details Added successfully",
            'data':
                {
                    'consultations_details': all_details,
                    'personal_details': personal_details,
                    'self' : all_details_self

                },
            }

            return compress(response)   
      
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Add Consultation Details",
                        "errors": str(e)
                        })


class DoctorConsultationClass(viewsets.ModelViewSet):

    # authentication_classes = [JWTAuthenticationUser]
    # permission_classes = [IsAuthenticated ]
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle,UserRateThrottle]

    # Client Registration API 
    serializer_class = DoctorConsultationSerializer
    
    
    
    
    
    
    



    @csrf_exempt
    def BookAppointment(self, request):
        print("+++++++++++++++++++++++++++++In Booking 1+++++++++++++++++++++++++++++++")
        print(request.data)
    
        try:
            if "consultation_for" not in request.data:
                consultation_details = DoctorConsultationDetails()
                user_serial_data = DoctorConsultationDetailsInOneSerializer(
                    consultation_details, data=request.data
                )
                user_serial_data.is_valid(raise_exception=True)
                consultation_details = user_serial_data.save()
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to Add Consultation Details",
                "errors": str(e)
            })

        appointment = DoctorConsultation()

        try:
            user_id = request.data.get('user_id')
            cancellation_reason = request.data.get('cancellation_reason')
            consultation_id = request.data.get('consultation_id')

            if consultation_id:
                self.cancelAppointment_fromCreateConsultation(
                    request, consultation_id, user_id, cancellation_reason
                )

            user_serial_data = DoctorConsultationSerializer(appointment, data=request.data)
            org_branch_id = request.data.get('organization_branch_id')

            if org_branch_id != "undefined":
                print(org_branch_id)
                org_branch = OrganizationBranch.objects.get(id=org_branch_id)
                appointment.organization_branch_id = org_branch

            slot = DoctorSlot.objects.get(id=request.data['doctor_slot'])
            slot.freeze = True
            slot.save()

            print("+++++++++++++++++++++++++++++In Booking 1+++++++++++++++++++++++++++++++")

            if user_serial_data.is_valid(raise_exception=True):
                if "consultation_for" in request.data:
                    consult_details_id = DoctorConsultationDetails.objects.get(id=request.data.get('consultation_for'))
                    user_serial_data.save(consultation_for=consult_details_id, partial=True)
                else:
                    user_serial_data.save(consultation_for=consultation_details, partial=True)

                try:
                    user_folder = settings.MEDIA_ROOT
                    reports_files = request.data.getlist('reports', [])
                    report_types = request.data.getlist('report_types', [])


                    
                    # Ensure both lists have the same length
                    if len(reports_files) != len(report_types):
                        return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Number of report files and types must match",
                        })

                    # Process each uploaded file and its associated report type
                    for report_file, report_type in zip(reports_files, report_types):
                        print(type(report_file))
                        # Perform actions with each file and its corresponding type
                        filename = f'/employee/consultation/reports/{report_type}_{appointment.id}_{report_file.name}'
                        file_path = user_folder + filename
                        with open(file_path ,'wb') as f:
                            f.write(report_file.read())

                        try:
                            # Create ConsultationReport object
                            consultation = DoctorConsultation.objects.get(id=appointment.id)
                            ConsultationReport.objects.create(
                                consultation=consultation,
                                report_type=report_type,
                                reports=filename
                            )
                        except Exception as e:
                            print(e)
                            return JsonResponse({
                                "success": False,
                                "status": status.HTTP_400_BAD_REQUEST,
                                "message": "Failed to create ConsultationReport",
                                "errors": str(e)
                            })
    # t = threading.Thread(target=long_process, args=(consultation.id, user_folder, filename))
                        # t.setDaemon(True)
                        # t.start()

                    slot_details = DoctorSlot.objects.get(id=request.data['doctor_slot'])
                    emails = []
                    try:
                        doctor_details = User.objects.get(id=request.data['doctor_id'])
                        emails.append({'email': str(doctor_details.email)})

                        try:
                            notification = Notification.objects.create(
                                user_id=request.user,
                                where_to="doctorcunsultation",
                                notification_msg=f"You have consultation",
                                action_content_type=ContentType.objects.get_for_model(DoctorConsultation),
                                action_id=appointment.id
                            )

                            notification.notification_to.set([doctor_details])
                            Redirect_to.objects.create(notification=notification, link="/doctor")
                        except Exception as e:
                            pass

                    except:
                        pass
                    try:
                        employee_details = User.objects.get(id=request.data['employee_id'])
                        emails.append({'email': str(employee_details.email)})

                    except:
                        pass
                    emails.append({'email': str("kar.rushikesh@gmail.com")})

                    url, uuid, id = create_zoom_meeting("Doctor Consultation", str(slot_details.date), emails)

                    update_meeting_link = DoctorConsultation.objects.get(id=appointment.id)
                    print(update_meeting_link)
                    update_meeting_link.meeting_url = url
                    update_meeting_link.meeting_id = id
                    update_meeting_link.meeting_uuid = uuid
                    update_meeting_link.save()

                    return JsonResponse({
                        "success": True,
                        "status": status.HTTP_201_CREATED,
                        "message": "Doctor Consultation Booked successfully",
                        'data': {
                            'consultation_id': appointment.id
                        }
                    })

                except Exception as e:
                    print("------e 212")
                    print(e)
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Failed to Book ssss Consultation",
                        "errors": str(e)
                    })

        except Exception as e:
            print(e)
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to Book sdf Doctor Consultation",
                "errors": str(e)
            })

    
    @csrf_exempt
    def AddReport(self, request):
        try:
            appointment_id = request.data.get('appointment_id')
            user_folder = settings.MEDIA_ROOT
            print("there--------------------------------")

            # reports_files_str = request.POST.get('reports', '')  # Comma-separated string
            # report_types_str = request.POST.get('report_types', '')  # Comma-separated string

            # reports_files = reports_files_str.split(',') if reports_files_str else []
            # report_types = report_types_str.split(',') if report_types_str else []
            reports_files = request.data.getlist('reports', [])
            report_types = request.data.getlist('report_types', [])

            
            print(reports_files)
            print(type(reports_files))

            print(report_types)
            
            # Ensure both lists have the same length
            if len(reports_files) != len(report_types):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Number of report files and types must match",
                })

            # Process each uploaded file and its associated report type
            for report_file, report_type in zip(reports_files, report_types):
                print(type(report_file))
                # Perform actions with each file and its corresponding type
                filename = f'/employee/consultation/reports/{report_type}_{appointment_id}_{report_file.name}'
                file_path = user_folder + filename
                with open(file_path ,'wb') as f:
                    f.write(report_file.read())

                try:
                    # Create ConsultationReport object
                    consultation = DoctorConsultation.objects.get(id=appointment_id)
                    ConsultationReport.objects.create(
                        consultation=consultation,
                        report_type=report_type,
                        reports=filename
                    )
                except Exception as e:
                    print(e)
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Failed to create ConsultationReport",
                        "errors": str(e)
                    })

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Reports added successfully",
            })

        except Exception as e:
            print("------e 212")
            print(e)
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to add reports",
                "errors": str(e)
        })

    @csrf_exempt
    def cancelAppointment_fromCreateConsultation(self, request,consultation_id, user_id, cancellation_reason):
        try:
            
            print("---------------sukh detailed")
            
            user=User.objects.get(id=user_id)
            # print(user.user_role)

            appointment = DoctorConsultation.objects.get(
                id=consultation_id)
            
            
            

            if user.user_role=="Dev::Employee": 
                    
                    
                cancel_limit = EmployeeCancelConsultationLimit.objects.create(
                consultation=appointment,
                employee_id=user
                )



            if appointment.confirmed == '0':
              
              
                # Unfreeze the slot if the appointment is not confirmed
                doctor_slot_id = appointment.doctor_slot
                doctor_slot = DoctorSlot.objects.get(id=doctor_slot_id.id)
                doctor_slot.freeze = False
                doctor_slot.save()
                
                appointment.status = "Cancelled"
                appointment.confirmed = "2"
                appointment.cancellation_reason = cancellation_reason
                appointment.cancelled_by=user
                appointment.save()
                # appointment.delete()
                
                    
            else:
                
                try:

                    # Update status and add cancellation reason for confirmed appointments
                    appointment.status = "Cancelled"
                    appointment.confirmed = "2"
                    appointment.cancellation_reason = cancellation_reason
                    appointment.cancelled_by=user
                    appointment.save()
                except Exception as e:
                    print("---------------d------------------getting error")
                    print(e)
                    
                

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Appointment cancelled successfully"
            })

        except DoctorConsultation.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Appointment not found.",
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to cancel appointment.",
                "errors": str(e)
            })

    @csrf_exempt
    def BookAppointmentForReport(self,request):
        print(request.data)
        appointment=DoctorConsultation()
        try:
            appointment.meeting_url  = generateMeeting(request.data['appointment_date'] + 'T' + request.data['appointment_time'])
            userSerialData = DoctorConsultationSerializer(appointment,data=request.data)
            try:
                if userSerialData.is_valid(raise_exception=True):
                    userSerialData.save()
                    


                    user_folder = settings.MEDIA_ROOT
                    print(request.data)
                    print("111111111111111")       
                    image = request.FILES.get('reports')
                    print("222222222222222")       

                    try:
                        if len(image)  > 5:
  
                            filename =  '/consultation/report_' + ''.join(random.choices('0123456789', k=12))  +   str(appointment.id) + image.name
                            with open(user_folder + filename, 'wb') as f:
                                f.write(image.read())

                        consultation = DoctorConsultation.objects.get(id=appointment.id)
                        consultation.reports = filename
                        consultation.save()


                    except:
                        pass

                        # Create and save the png file 
                        

                    return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "Doctor Consultation Booked successfully",
                    'data':
                        {
                            'consultation_id': appointment.id
                        }
                    })        
            except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Book Doctor Consultation",
                        "errors": str(e)
                        })
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Book Doctor Consultation",
                        "errors": str(e)
                        })


    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('consultation_id', openapi.IN_QUERY, description="Appointment ID", type=openapi.TYPE_INTEGER,default=24)
    ]) 
    @csrf_exempt
    def GetBookingDetails(self,request):

        try:

            appointment=DoctorConsultation.objects.filter(id = request.GET.get("consultation_id"))


            userSerialData = ShowDoctorConsultationSerializer(appointment,many = True)
            details = json.loads(json.dumps(userSerialData.data))
                    

            return JsonResponse({
            "success": True,
            "status": status.HTTP_201_CREATED,                
            "message": "Doctor Consultation Booked successfully",
            'data':
                {
                    'consultation_details': details
                }
            })        

        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Book Doctor Consultation",
                        "errors": str(e)
                        })

    
    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('user_id', openapi.IN_QUERY, description="Parameter User ID", type=openapi.TYPE_INTEGER,default=2),
    ]) 
    @csrf_exempt
    def GetConsultationList(self,request):
        print(request.GET)                                                                                                                                                                                                        
        try:
            addNew = False

            consultationDetails=DoctorConsultation.objects.filter( Q(status = 'Booked') | Q(status = 'Rescheduled'), employee_id = request.GET.get('user_id') ).order_by('-appointment_date')
            userSerialData = ShowDoctorConsultationSerializer(consultationDetails, many=True)
            upcoming = json.loads(json.dumps(userSerialData.data))


            consultationDetails=DoctorConsultation.objects.filter( status = 'Cancelled', employee_id = request.GET.get('user_id') ).order_by('-appointment_date')
            userSerialData = ShowDoctorConsultationSerializer(consultationDetails, many=True)
            cancelled = json.loads(json.dumps(userSerialData.data))
            

            consultationDetails=DoctorConsultation.objects.filter( status = 'Completed', employee_id = request.GET.get('user_id') ).order_by('-appointment_date')
            userSerialData = ShowDoctorConsultationSerializer(consultationDetails, many=True)
            completed = json.loads(json.dumps(userSerialData.data))

            response={
                      "success": True,
            "status": status.HTTP_201_CREATED,                
            "message": " Consultation Details Added successfully",
            'data':
                {
                    'upcoming': upcoming,
                    'cancelled': cancelled,
                    'completed': completed,


                },
            }

            return compress(response)
            
                  
      
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Add Consultation Details",
                        "errors": str(e)
                        })



    
    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('user_id', openapi.IN_QUERY, description="User ID", type=openapi.TYPE_INTEGER,default=24),
    openapi.Parameter('appointment_date', openapi.IN_QUERY, description="Appointment Date", type=openapi.TYPE_STRING,default=24),
    openapi.Parameter('appointment_time', openapi.IN_QUERY, description="Appointment Time", type=openapi.TYPE_STRING,default=24)
    ])
    @csrf_exempt
    def getDoctor(self,request):
        print("-----------------dd---------------")
        print(request.data)
        try:
            
            appointment=list(User.objects.filter(user_role__contains = "Doctor" ).values_list('id'))
            doctor_ids = []
            for data in appointment:
                doctor_ids.append(data[0])
            print(appointment)
            doctors =  DoctorPersonalDetails.objects.filter(user_id__in = appointment)
            doctorDetails = ShowDoctorPersonalDetailsSerializer(doctors, many = True)
            details = json.loads(json.dumps(doctorDetails.data))

            return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,                
            "message": "Appointment updated successfully",
            'data':
                {
                    'doctors': details
                }
            })
                            
     
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to update Appointment Details",
                        "errors": str(e)
                        })


  
class UpdateDoctorConsultationClass(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthenticationUser]
    permission_classes = [IsAuthenticated ]
    # permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle,UserRateThrottle]

    # Client Registration API 
    serializer_class = UpdateDoctorConsultationSerializer
    
    @csrf_exempt
    def updateAppointment(self,request):
        print("---------------hhhhhh-----------------")
        print(request.data)
        try:
            appointment=DoctorConsultation.objects.get(id=request.data['consultation_id'])
            appointmentData = UpdateDoctorConsultationSerializer(appointment,data=request.data)
            
            
            
            
            
            try:
                print("trying=----------------------------")
                
                if appointmentData.is_valid(raise_exception=True):
                    print("----------hey thereeee--------")

                    appointmentData.save()
                    print("------------------as ")
                    print(appointmentData.status)
                    
                    if appointmentData.status=="Cancelled":
                    
                        try:
                            notification = Notification.objects.create(
                            user_id=request.user,
                            notification_msg=f"Your Consultation is Cancelled by Doctor",
                            action_content_type=ContentType.objects.get_for_model(DoctorConsultation),
                            action_id=appointmentData.id
                            
                            )
                            
                            notification.notification_to.set([appointmentData.employee_id])
            
                            
    
                            Redirect_to.objects.create(notification=notification, link="/employee")
                        except Exception as e:
                            print("=------j-----------")
                            print(e)
                            pass
                    else:
                    
                    
                    
                        try:
                            notification = Notification.objects.create(
                            user_id=request.user,
                            notification_msg=f"Your Consultation is Approved by Doctor",
                            action_content_type=ContentType.objects.get_for_model(DoctorConsultation),
                            action_id=appointmentData.id,
                            where_to="consultation"
                            )
                            
                            notification.notification_to.set([appointmentData.employee_id])
            
                            
    
                            Redirect_to.objects.create(notification=notification, link="/employee/doctorConsultation")
                        except Exception as e:
                            print("=------j-jjg----------")
                            print(e)
                            pass
                      

                    return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,                
                    "message": "Appointment updated successfully",
                    'data':
                        {
                            'consultation_id': appointment.id
                        }
                    })
                            
            except Exception as e:
            
                print("---------------me pn")
                print(e)
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to update Appointment Details",
                        "errors": str(e)
                        })
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to update Appointment Details",
                        "errors": str(e)
                        })


class RescheduleConsultationClass(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthenticationUser]
    permission_classes = [IsAuthenticated ]
    # permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle,UserRateThrottle]

    serializer_class = RescheduleConsultaionSerializer
    @csrf_exempt
    def rescheduleAppointment(self,request):
        print("--------------------------------")
        print(request.data)
        try:
            appointment=DoctorConsultation.objects.get(id=request.data['consultation_id'])
            appointmentData = RescheduleConsultaionSerializer(appointment,data=request.data)
            try:
                
                if appointmentData.is_valid(raise_exception=True):
                    if appointment.reschedule_appointment is None:
                        appointmentData.save()
                    else:
                        
                        return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Appointment already Rescheduled",
                        "errors": str(e)
                        })
   
                    return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,                
                    "message": "Appointment Rescheduled successfully",
                    'data':
                        {
                            'consultation_id': appointment.id
                        }
                    })
                            
            except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Reschedule Appointment",
                        "errors": str(e)
                        })
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Reschedule Appointment",
                        "errors": str(e)
                        })



class DoctorsViewSet(viewsets.ModelViewSet):

    serializer_class = RescheduleConsultaionSerializer

    @csrf_exempt
    def get_available_doctors(self,request):
        try:
            print("----hey")
            meeting_mode = request.GET.get('meeting_mode')
            organization_id = request.GET.get('organization_id')
            branch_id = request.GET.get('branch_id')
            input_date = request.GET.get('date')

            if not meeting_mode or not organization_id or not input_date:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Invalid request. meeting_mode, organization_id, and date are required."
                })

            today = date.today()
            input_date = date.fromisoformat(input_date)

            if input_date < today:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Invalid date. Date should be today or a future date."
                })

            if meeting_mode == "Online":
                doctors = DoctorSlot.objects.filter(
                    organization_id=organization_id,
                    date=input_date,
                ).values_list('doctor', flat=True)
            else:
                if not branch_id:
                    return JsonResponse({
                        "success": False,
                        "status": 400,
                        "message": "Invalid request. branch_id is required for offline meeting_mode."
                    })

                doctors = DoctorSlot.objects.filter(
                    organization_id=organization_id,
                    organization_branch_id=branch_id,
                    date=input_date,
                    meeting_mode="Offline"
                ).values_list('doctor', flat=True)

            available_doctors = DoctorPersonalDetails.objects.filter(id__in=doctors)
            serializer = DoctorPersonalDetailsSerializer(available_doctors, many=True)

            return JsonResponse({
                "success": True,
                "status": 200,
                "message": "Available doctors retrieved successfully.",
                "data": serializer.data
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": "Failed to retrieve available doctors.",
                "errors": str(e)
            })



def long_process(consultation_id, user_folder, filename):
    try:
        
        
        pdf_reader = PdfReader(user_folder + filename)
        

        if len(pdf_reader.pages) > 0:
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text()

            tokenizer = AutoTokenizer.from_pretrained("slauw87/bart_summarisation")
            model = AutoModelForSeq2SeqLM.from_pretrained("slauw87/bart_summarisation")

            input_ids = tokenizer.encode(pdf_text, return_tensors="pt", max_length=1024, truncation=True)

            summary_ids = model.generate(input_ids, max_length=300, min_length=150, length_penalty=2.0, num_beams=4, early_stopping=True)

            summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            
            consultation = DoctorConsultation.objects.get(id=consultation_id)
           
            
            
            consultation.summery = summary
            consultation.save()
            
            
    except Exception as e:
        print(e)


class DoctorConsultationForFilterClass(viewsets.ModelViewSet):

    @csrf_exempt
    def getFriendsndFamily(self, request):
        
        user_id = request.GET.get('user_id')
        
        user = get_object_or_404(User, id=user_id)

        
        doctor_consultation_details = DoctorConsultationDetails.objects.filter(employee_id=user)

        # Use annotate and distinct to get distinct full_name and count
        distinct_data = doctor_consultation_details.values('full_name').annotate(count=Count('full_name')).order_by('full_name')

        # Sort the data based on the length of the full_name to get the longest one
        distinct_data = sorted(distinct_data, key=lambda x: len(x['full_name']), reverse=True)

        serializer = DoctorConsultationDetailsForFilterSerializer(distinct_data, many=True)

        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "Doctor Consultation Details retrieved successfully.",
            "data": serializer.data
        })
        
    @csrf_exempt
    def getReportType(self, request):
        user_id = request.GET.get('user_id')
        user = get_object_or_404(User, id=user_id)

        consultations = DoctorConsultation.objects.filter(employee_id=user).prefetch_related('consultation_reports')

        # Filter out consultations without reports
        consultations_with_reports = [consultation for consultation in consultations if consultation.consultation_reports.filter(reports__isnull=False).exclude(reports='').exists()]

        serializer = DoctorConsultationFilterSerializer(consultations_with_reports, many=True)

        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "Doctor Consultation Details retrieved successfully.",
            "data": serializer.data
        })



class EmployeeConsultationCountClass(viewsets.ModelViewSet):

    @csrf_exempt
    def getCancellationCount(self, request):
        user_id = request.GET.get('user_id')
        consultation_id = request.GET.get('consultation_id')         
        try:
            user=User.objects.get(id=user_id)
            appointment = DoctorConsultation.objects.get(
                Q(employee_id=user_id),
                id=consultation_id)
            current_month_year = date.today().strftime('%Y-%m')
            if user.user_role == "Dev::Employee" and EmployeeCancelConsultationLimit.objects.filter(employee_id=user, cancel_date__startswith=current_month_year).count() >= 2:
                    return JsonResponse({
                        "success": False,
                        "status": 121,
                        "message": "Unfortunately, you have exceeded the allowed limit for canceling appointments.",
                    })
            else:
                return JsonResponse({
                        "success": True
                    })
        
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": "Failed to Count",
                "errors": str(e)
            }) 
            
            

class DownloadReportClass(viewsets.ModelViewSet):


        
    @csrf_exempt 
    def downloadReportsPDF(self, request):
        user_id = request.GET.get('user_id')
        consultation_id = request.GET.get('consultation_id')

        if not consultation_id:
            return JsonResponse({
                'error': 'Consultation ID is required.'
            }, status=400)

        try:
            consultation_ids = [int(id) for id in consultation_id.split(',')]
            reports_data = ConsultationReport.objects.filter(consultation_id__in=consultation_ids)

            if not reports_data:
                return JsonResponse({
                    'error': 'No reports found for the given consultation IDs.'
                }, status=404)

            pdf_data = BytesIO()
            pdf_writer = PyPDF2.PdfWriter()  # This line needs to be corrected

            for report_data in reports_data:
                consultation = DoctorConsultation.objects.get(id=report_data.consultation_id)
                full_name = consultation.consultation_for.full_name
                report_type = report_data.report_type
                title = f"Consultation for {full_name} - {report_type}"
                


                # Construct the server path
                server_path = os.path.join("/home/ubuntu/Production/backend/digielves-dev/media", str(report_data.reports))

                # Print the file path for debugging
                print(f"File Path: {server_path}")
                print(settings.MEDIA_ROOT)

                # Check if the file exists
                if os.path.exists(f'/home/ubuntu/Production/backend/digielves-dev/media{report_data.reports}'):
                    print("----------hmm")
                    with open(f'/home/ubuntu/Production/backend/digielves-dev/media{report_data.reports}', 'rb') as report_file:
                        pdf_reader = PyPDF2.PdfReader(report_file)
                        
                        for pdf_page in pdf_reader.pages:
                            pdf_writer.add_page(pdf_page)
                        
#                        title_page_data = BytesIO()
#                        title_page = canvas.Canvas(title_page_data)
#                        title_page.drawString(100, 780, title)
#                        title_page.drawString(100, 10, f"Report Type: {report_type}")
#                        title_page.save()
#    
#                        # Merge the new page with the existing PDF
#                        title_page_data.seek(0)
#                        title_pdf_reader = PyPDF2.PdfReader(title_page_data)
#                        pdf_writer.add_page(title_pdf_reader.pages[0])
                        
                        
                        
            pdf_writer.write(pdf_data)
            pdf_data.seek(0)
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="consultation_reports.pdf"'
                        
            return response
        except Exception as e:
            return JsonResponse({
                'error': f'An error occurred: {str(e)}'
            }, status=500)
