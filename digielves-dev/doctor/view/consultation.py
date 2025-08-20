import base64
import json
import random
from django.shortcuts import render
from configuration.authentication import JWTAuthenticationUser
from configuration.generateGoogleMeet import generateMeeting
from configuration.generatePrescriptionPDF import generate_prescription
from configuration.gzipCompression import compress
from digielves_setup.models import DoctorConsultation, DoctorConsultationDetails, DoctorPersonalDetails, DoctorPrescriptions, DoctorSlot, EmployeeCancelConsultationLimit, EmployeePersonalDetails, OrganizationDetails, Redirect_to, Notification, User, notification_handler
from digielves_setup.validations import is_valid_image
from doctor.seriallizers.doctor_serillizer import DoctorPersonalDetailsSerializer, ShowDoctorPersonalDetailsSerializer
from doctor.seriallizers.prescription import ShowDoctorPrescriptionsSerializer
from doctor.view.prescription import DoctorPrescriptionClass
from employee.seriallizers.doctor_consultation_serializer import DoctorConsultationDetailsForFilterSerializer, DoctorConsultationDetailsSerializer, DoctorConsultationSerializer, RescheduleConsultaionSerializer, ShowDoctorConsultation_Serializer, ShowDoctorConsultationDetailsSerializer, ShowDoctorConsultationInDoctorSerializer, ShowDoctorConsultationSerializer, UpdateDoctorConsultationSerializer
from django.db.models import Count
from employee.seriallizers.notification_serillizer import NotificationSerializer


from rest_framework import viewsets
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status

# Authentication Modules for rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.permissions import  IsAuthenticated ,AllowAny
from django.db.models import Q
from django.db.models import Max

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from datetime import date
import threading
import time
import asyncio
from django.contrib.contenttypes.models import ContentType
from configuration.zoomMeetingRecording import getTeamRecording

from datetime import datetime

import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save

class DoctorConsultationClass(viewsets.ModelViewSet):

    authentication_classes = [JWTAuthenticationUser]
    permission_classes = [IsAuthenticated ]
    # permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle,UserRateThrottle]


    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('consultation_id', openapi.IN_QUERY, description="Appointment ID", type=openapi.TYPE_INTEGER,default=24)
    ]) 
    @csrf_exempt
    def GetBookingDetails(self,request):
        print("_______________________________")
        try:

            appointment=DoctorConsultation.objects.filter(id = request.GET.get("consultation_id"))


            userSerialData = ShowDoctorConsultation_Serializer(appointment,many = True)
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

        # try:

        #     appointment=DoctorConsultation.objects.filter(id = request.GET.get("consultation_id"))


        #     userSerialData = ShowDoctorConsultationDetailsSerializer(appointment, many=True)
        #     details = json.loads(json.dumps(userSerialData.data))
                    

        #     return JsonResponse({
        #     "success": True,
        #     "status": status.HTTP_201_CREATED,                
        #     "message": "Doctor Consultation Details",
        #     'data':
        #         {
        #             'consultation_details': details
        #         }
        #     })        

        # except Exception as e:
        #         return JsonResponse({
        #                 "success": False,
        #                 "status": status.HTTP_400_BAD_REQUEST, 
        #                 "message": "Failed to Fetch Doctor Consultation Details",
        #                 "errors": str(e)
        #                 })




    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('user_id', openapi.IN_QUERY, description="Parameter User ID", type=openapi.TYPE_INTEGER,default=2),
    openapi.Parameter('doctor_id', openapi.IN_QUERY, description="Parameter User ID", type=openapi.TYPE_INTEGER,default=4),

    ]) 
    @csrf_exempt
    def GetDoctorConsultation(self,request):
        print(request.GET)                                                                                                                                                                                                        
        try:
            


            scheduledCount=DoctorConsultation.objects.filter( Q(status = 'Booked') | Q(status = 'Rescheduled'),confirmed = 1, doctor_id = request.GET.get('user_id') ).count()
            


            cancelledCount=DoctorConsultation.objects.filter( status = 'Cancelled', doctor_id = request.GET.get('user_id') ).count()
            


            completedCount=DoctorConsultation.objects.filter( status = 'Completed', doctor_id = request.GET.get('user_id') ).count()
            
            
            consultationDetails=DoctorConsultation.objects.filter(  Q(status = 'Booked') | Q(status = 'Rescheduled'), confirmed = 1, doctor_id = request.GET.get('user_id') ).order_by('appointment_date')
            userSerialData = ShowDoctorConsultationSerializer(consultationDetails, many=True)
            appointmnets = json.loads(json.dumps(userSerialData.data))
            

            consultationDetails=DoctorConsultation.objects.filter(  Q(status = 'Booked') | Q(status = 'Rescheduled'), confirmed = 0, doctor_id = request.GET.get('user_id') )
            userSerialData = ShowDoctorConsultationSerializer(consultationDetails, many=True)
            appointmnetsRequests = json.loads(json.dumps(userSerialData.data))
            
            total = scheduledCount+cancelledCount+completedCount
            print(scheduledCount)
            print(cancelledCount)
            print(completedCount)
            
            return JsonResponse({
            "success": True,
            "status": status.HTTP_201_CREATED,                
            "message": " Consultation List",
            'data':
                {
                    
                    'apointment_count' : 
                          {
                            'total' : total,
                            'scheduled': scheduledCount,
                            'cancelled': cancelledCount,
                            'completed': completedCount,
                          },
                    'apointment_percentage' : 
                          {
                            'scheduled': 0 if scheduledCount == 0 else round(((scheduledCount)/total) * 100,2),
                            'cancelled': 0 if cancelledCount == 0 else round(((cancelledCount)/total) * 100,2) ,
                            'completed': 0 if completedCount == 0 else round(((completedCount)/total) * 100,2)  ,
                          },
                          
                    'appointmnets' : appointmnets,
                    'appointmentRequest' : appointmnetsRequests
                    
                },
            })        
      
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Fetch List",
                        "errors": str(e)
                        })



    
    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('user_id', openapi.IN_QUERY, description="Parameter User ID", type=openapi.TYPE_INTEGER,default=2),
    openapi.Parameter('doctor_id', openapi.IN_QUERY, description="Parameter User ID", type=openapi.TYPE_INTEGER,default=4),

    ]) 
    @csrf_exempt
    def GetCompletedConsultationList(self,request):
        print(request.GET)                                                                                                                                                                                                        
        try:


            consultationDetails=DoctorConsultation.objects.filter( status = 'Completed', doctor_id = request.GET.get('doctor_id') )
            userSerialData = ShowDoctorConsultationSerializer(consultationDetails, many=True)
            completed = json.loads(json.dumps(userSerialData.data))
            
            return JsonResponse({
            "success": True,
            "status": status.HTTP_201_CREATED,                
            "message": " Consultation List",
            'data':
                {
        
                    'completed': completed,


                },
            })        
      
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Fetch List",
                        "errors": str(e)
                        })



    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('user_id', openapi.IN_QUERY, description="Parameter User ID", type=openapi.TYPE_INTEGER,default=2),
    openapi.Parameter('doctor_id', openapi.IN_QUERY, description="Parameter User ID", type=openapi.TYPE_INTEGER,default=4),

    ]) 
    @csrf_exempt
    def GetCompletedAndUpcomingConsultationList(self,request):
        print(request.GET)                                                                                                                                                                                                        
        try:


            consultationDetails=DoctorConsultation.objects.filter( status = 'Completed', doctor_id = request.GET.get('doctor_id') )
            userSerialData = ShowDoctorConsultationInDoctorSerializer(consultationDetails, many=True)
            completed = json.loads(json.dumps(userSerialData.data))

            consultationDetails=DoctorConsultation.objects.filter(Q(status = 'Booked') | Q(status = 'Rescheduled'),confirmed = 1, doctor_id = request.GET.get('doctor_id') )
            userSerialData = ShowDoctorConsultationInDoctorSerializer(consultationDetails, many=True)
            upcoming = json.loads(json.dumps(userSerialData.data))

            consultationDetails=DoctorConsultation.objects.filter(status = 'Cancelled', doctor_id = request.GET.get('doctor_id') )
            userSerialData = ShowDoctorConsultationInDoctorSerializer(consultationDetails, many=True)
            cancelled = json.loads(json.dumps(userSerialData.data))
            
            return JsonResponse({
            "success": True,
            "status": status.HTTP_201_CREATED,                 
            "message": " Consultation List",
            'data':
                {
        
                    'completed': completed,
                    'upcoming' : upcoming ,
                    'cancelled': cancelled


                },
            })        
      
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Fetch List",
                        "errors": str(e)
                        })




    @csrf_exempt
    def DeleteDoctorPrescription(self, request):
        try:
            prescription_id = request.GET.get("prescription_id")
            
            # Check if the prescription exists
            prescription = DoctorPrescriptions.objects.filter(id=prescription_id).first()
            if not prescription:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Doctor prescription not found."
                })
            
            # Delete the prescription
            prescription.delete()
            
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Doctor prescription deleted successfully.",
                "prescription_id": prescription_id
            })
            
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to delete doctor prescription.",
                "errors": str(e)
            })


    
    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('user_id', openapi.IN_QUERY, description="Parameter User ID", type=openapi.TYPE_INTEGER,default=2),
    ]) 
    @csrf_exempt
    def GetConsultationList(self,request):
        print(request.GET)                                                                                                                                                                                                        
        try:

            consultationDetails=DoctorConsultation.objects.filter( Q(status = 'Booked') | Q(status = 'Rescheduled'),confirmed = 1, doctor_id = request.GET.get('user_id') )
            userSerialData = ShowDoctorConsultationSerializer(consultationDetails, many=True)
            upcoming = json.loads(json.dumps(userSerialData.data))


            consultationDetails=DoctorConsultation.objects.filter( status = 'Cancelled', doctor_id = request.GET.get('user_id') )
            userSerialData = ShowDoctorConsultationSerializer(consultationDetails, many=True)
            cancelled = json.loads(json.dumps(userSerialData.data))
            

            consultationDetails=DoctorConsultation.objects.filter( status = 'Completed', doctor_id = request.GET.get('user_id') )
            userSerialData = ShowDoctorConsultationSerializer(consultationDetails, many=True)
            completed = json.loads(json.dumps(userSerialData.data))
            
            return JsonResponse({
            "success": True,
            "status": status.HTTP_201_CREATED,                
            "message": " Consultation Details Added successfully",
            'data':
                {
                    'upcoming': upcoming,
                    'cancelled': cancelled,
                    'completed': completed,


                },
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

    openapi.Parameter('consultation_id', openapi.IN_QUERY, description="Parameter Consultation ID", type=openapi.TYPE_INTEGER,default=2),
    openapi.Parameter('status', openapi.IN_QUERY, description="Parameter Status", type=openapi.TYPE_STRING,default="Completed"),

    ]) 
    #@csrf_exempt
    def updateConsultationStatus(self,request):
        print(request.GET)  
        print("Update status API") 
        print(request.GET.get('consultation_id'))   
        new_status = request.POST.get('status')                                                                                                                                                                                                  
        try:

            consultationDetails=DoctorConsultation.objects.get( id = request.GET.get('consultation_id') )
            #consultationDetails.status = request.GET.get('status')
            #consultationDetails.save()
            
            
            
            notification = Notification.objects.create(
                user_id=request.user,
                notification_msg=f"Your doctor has joined the meeting. Please join now to start your consultation.",
                action_content_type=ContentType.objects.get_for_model(DoctorConsultation),
                action_id=consultationDetails.id
                
                )
                
            notification.notification_to.set([consultationDetails.employee_id])

            
            
                

            Redirect_to.objects.create(notification=notification, link=consultationDetails.meeting_url)
            consultion_task = threading.Thread(target=schedule_status_update, args=(consultationDetails,new_status) )
            consultion_task.setDaemon(True) 
            consultion_task.start() 
           
    
            return JsonResponse({
            "success": True,
            "status": status.HTTP_201_CREATED,                
            "message": " Consultation Status Updated successfully",
             })        
      
        except Exception as e:
            return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Update Consultation Status",
                        "errors": str(e)
                        })
                        
    


    @csrf_exempt
    def generateSummary(self,request):
        print(request.GET)     
        print("I am here---------------------------------------------")                                                                                                                                                                                                   
        try:
            print(request.GET.get('consultation_id'))
            consultationDetails=DoctorConsultation.objects.get( id = request.GET.get('consultation_id') )
            consultationDetails.status = 'Completed'
            consultationDetails.summery_generating=True
            consultationDetails.save()


            consultationDetails=DoctorConsultation.objects.get( id = request.GET.get('consultation_id') )
            summary = threading.Thread(target=getTeamRecording, args=(str(consultationDetails.meeting_uuid),str(consultationDetails.meeting_id),request.GET.get('consultation_id')) )
            summary.setDaemon(True) 
            summary.start() 

            
            return JsonResponse({
            "success": True,
            "status": status.HTTP_201_CREATED,                
            "message": " Consultation Status Updated successfully",
            })        
      
        except Exception as e:
            return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST, 
                    "message": "Failed to Update Consultation Status",
                    "errors": str(e)
                    })



  
class UpdateDoctorConsultationClass(viewsets.ModelViewSet):
    # authentication_classes = [JWTAuthenticationUser]
    # permission_classes = [IsAuthenticated ]
    # # permission_classes = [AllowAny]
    # throttle_classes = [AnonRateThrottle,UserRateThrottle]

    # Client Registration API 
    serializer_class = UpdateDoctorConsultationSerializer
    
    @csrf_exempt
    def TestApiGetPdf(self,request):
        prescription = DoctorPrescriptions.objects.filter(consultation_id = request.data['consultation_id'])
        userSerialData = ShowDoctorPrescriptionsSerializer(prescription, many=True)
        prescriptionData = json.loads(json.dumps(userSerialData.data))
        
        path = generate_prescription(prescriptionData,   request.data['consultation_id'])
                        
                        
        appointment=DoctorConsultation.objects.get(id=request.data['consultation_id'])
        
        appointment.prescription_url = path
        
        appointment.save()
        
        return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,                
                    "message": "Appointment updated successfully",
                
                    })

    @csrf_exempt
    def updateAppointment(self,request):
        
        print(request.data)
        try:
            appointment=DoctorConsultation.objects.get(id=request.data['consultation_id'])
            appointmentData = UpdateDoctorConsultationSerializer(appointment,data=request.data)
            try:
                
                if appointmentData.is_valid(raise_exception=True):
                    appointmentData.save()
                    
                    
                    print(appointmentData.validated_data.get('status'))
                    print(appointmentData.validated_data.get('status')=="Cancelled")
                    print(appointmentData.validated_data.get('status')=="Booked")
                    
                    if appointmentData.validated_data.get('status')=="Cancelled":
                        
                        try:

                            slot = DoctorSlot.objects.filter(id=appointment.doctor_slot.id).first()

                            slot.freeze = False
                            slot.save()

                            appointment.doctor_slot = None
                            appointment.save()
                            
                            
                            notification = Notification.objects.create(
                            user_id=request.user,
                            notification_msg=f"Your Consultation is Cancelled by Doctor",
                            action_content_type=ContentType.objects.get_for_model(DoctorConsultation),
                            action_id=appointment.id
                            
                            )
                            
                            notification.notification_to.set([appointment.employee_id])
                            
                            
                            # channel_layer = get_channel_layer()
                            # async_to_sync(channel_layer.group_send)(
                            #     f"user_{request.user}",
                            #     {"type": "send_notification", "message": NotificationSerializer(notification).data},
                            # )

                            Redirect_to.objects.create(notification=notification, link="/employee")
                        except Exception as e:
                            
                            pass
                    elif appointmentData.validated_data.get('status')=="Booked":
                        try:
                            notification = Notification.objects.create(
                            user_id=request.user,
                            notification_msg=f"Your Consultation is Approved by Doctor",
                            action_content_type=ContentType.objects.get_for_model(DoctorConsultation),
                            action_id=appointment.id,
                            where_to="consultation"
                            )
                            
                            notification.notification_to.set([appointment.employee_id])

                            channel_layer = get_channel_layer()
                            async_to_sync(channel_layer.group_send)(
                                f"user_{request.user}",
                                {"type": "send_notification", "message": NotificationSerializer(notification).data},
                            )
                            
    
                            Redirect_to.objects.create(notification=notification, link="/employee/doctorConsultation")
                        except Exception as e:
                           
                            pass
                    
                    else:
                        pass

            
                    prescription = DoctorPrescriptions.objects.filter(consultation_id = request.data['consultation_id'])
                    userSerialData = ShowDoctorPrescriptionsSerializer(prescription, many=True)
                    prescriptionData = json.loads(json.dumps(userSerialData.data))
                    
                    consultation = DoctorConsultation.objects.filter(id=request.data['consultation_id'])
                    consultation = ShowDoctorConsultationSerializer(consultation, many=True)
                    consultationData = json.loads(json.dumps(consultation.data))
                    
                    # print(consultationData)
                    if len(prescriptionData) > 0:
                        
                        path = generate_prescription(prescriptionData,   request.data['consultation_id'])
                        
                        
                        appointment=DoctorConsultation.objects.get(id=request.data['consultation_id'])
                        
                        appointment.prescription_url = path
                        
                        appointment.save()

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



class CancelConsultationClass(viewsets.ModelViewSet):
    
    @csrf_exempt
    def cancelAppointment(self, request):
        try:
            print(request.data)
            user_id = request.data.get('user_id')
            
            
            cancellation_reason = request.data.get('cancellation_reason')
            hasTo_unfreeze = request.data.get('unfreeze')

            consultation_id = request.data.get('consultation_id')         
            
            user=User.objects.get(id=user_id)
            print(user.user_role)
            appointment = DoctorConsultation.objects.get(
                Q(doctor_id=user_id) | Q(employee_id=user_id),
                id=consultation_id)


            if appointment.confirmed == '1' and user.user_role=="Dev::Employee":

                EmployeeCancelConsultationLimit.objects.create(
                consultation=appointment,
                employee_id=user
                )
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
                try:
                    cancel_reason = request.data.get('cancellation_reason', 'No reason provided')
                    noti_msg = f"The Employee has canceled the consultation. Reason: {cancel_reason}"
                    post_save.disconnect(notification_handler, sender=Notification)
                    notification = Notification.objects.create(
                        user_id=user,
                        where_to="cancelled_by_emp",
                        notification_msg=noti_msg,
                        action_content_type=ContentType.objects.get_for_model(DoctorConsultation),
                        action_id=consultation_id
                    )
                    notification.notification_to.set([appointment.doctor_id])
                    post_save.connect(notification_handler, sender=Notification)
                    post_save.send(sender=Notification, instance=notification, created=True)
                        
                        
                except Exception as e:
                    print("Notification creation failed:", e)
                
                
                
               
            elif user.user_role=="Dev::Doctor":

                # Update status and add cancellation reason for confirmed appointments
                appointment.status = "Cancelled"
                appointment.confirmed = "2"
                
                
                
 
                appointment.cancellation_reason = cancellation_reason
                appointment.cancelled_by=user
                if 'reschedule_date' in request.data:
                    if request.data.get('reschedule_date')!="":
                        appointment.reschedule_date = request.data.get('reschedule_date')
                    else:
                        pass

                if 'reschedule_time' in request.data:
                    if request.data.get('reschedule_date')!="":
                        appointment.reschedule_time = request.data.get('reschedule_time') 
                    else:
                        pass
                
                if request.data.get('reschedule_date')!="" and request.data.get('reschedule_date')!="":
                    noti_msg = f"The doctor has canceled the consultation. You can reschedule for {request.data.get('reschedule_date')} at {request.data.get('reschedule_time')}."
                else:
                    cancel_reason = request.data.get('cancellation_reason', 'No reason provided')
                    noti_msg = f"The doctor has canceled the consultation. Reason: {cancel_reason}"
          
                try:
                    post_save.disconnect(notification_handler, sender=Notification)
                    notification = Notification.objects.create(
                        user_id=user,
                        where_to="reschedule_consult",
                        notification_msg=noti_msg,
                        action_content_type=ContentType.objects.get_for_model(DoctorConsultation),
                        action_id=consultation_id
                    )
                    notification.notification_to.set([appointment.employee_id])
                    post_save.connect(notification_handler, sender=Notification)
                    post_save.send(sender=Notification, instance=notification, created=True)
                        
                        
                except Exception as e:
                    print("Notification creation failed:", e)
                    
            elif appointment.confirmed == '0' and user.user_role=="Dev::Employee":
                appointment.status = "Cancelled"
                appointment.confirmed = "2"
              
                appointment.cancellation_reason = cancellation_reason

                appointment.cancelled_by=user
              
                    
                    
                
            if hasTo_unfreeze:
                print("----------true")
                doctor_slot_id = appointment.doctor_slot
                print(doctor_slot_id)
                doctor_slot = DoctorSlot.objects.get(id=doctor_slot_id.id)
                doctor_slot.freeze = False
                appointment.doctor_slot = None
                appointment.save()
                doctor_slot.save()
            else:
                appointment.save()
                

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
    def GetDoctorAvailableDate(self, request):
        try:
            user_id = request.GET.get('user_id')
            consultation_id = request.GET.get('consultation_id')
            
            appointment = DoctorConsultation.objects.get(id=consultation_id)
            
            doctor = DoctorPersonalDetails.objects.filter(user_id_id=user_id).first()
            
            filters = Q(doctor=doctor, freeze=False, meeting_mode=appointment.meeting_pref_type, organization=appointment.organization_id)
            
            if appointment.meeting_pref_type != "Online":
                filters &= Q(organization_branch=appointment.organization_branch_id)
            
            # Filter out past dates
            filters &= Q(date__gte=date.today())
            
            available_dates = DoctorSlot.objects.filter(filters).values('date').annotate(count=Count('date')).order_by('date')
                
            dates_data = [{'date': date['date'], 'count': date['count']} for date in available_dates]

            return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Available Dates Fetched Successfully",
                'data': dates_data
            })

        except DoctorConsultation.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "DoctorConsultation not found.",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to Fetch Available Dates",
                "errors": str(e)
            })
            
    
    @csrf_exempt
    def GetAvailableSlots(self, request):
        try:
            user_id = request.GET.get('user_id')
            selected_date = request.GET.get('date')
            
            doctor = DoctorPersonalDetails.objects.get(user_id_id=user_id)
            current_datetime = datetime.now()  # Get the current date and time
            current_date = current_datetime.date()
            current_time = current_datetime.time()
            formatted_current_time = f"{current_time.hour:02d}:{current_time.minute:02d}"
            
            available_slots = DoctorSlot.objects.filter(doctor=doctor, date=selected_date, freeze=False).exclude(date=current_date, slots__lt=f"{formatted_current_time}:").values('id', 'slots')
            
            
            
            slots_data = [{'id': slot['id'], 'slots': slot['slots']} for slot in available_slots]

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Slots retrieved successfully.",
                "data": slots_data
            })

        except DoctorPersonalDetails.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "DoctorPersonalDetails not found for the given user_id.",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve available slots.",
                "errors": str(e)
            })
            
    



def schedule_status_update(consultation, new_status):
        
        time.sleep(1200)
        
        
        consultation.status = "Completed"
        consultation.save()
