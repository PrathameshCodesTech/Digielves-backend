
from digielves_setup.models import DoctorConsultation, DoctorConsultationDetails, DoctorPrescriptions
from rest_framework import serializers



class DoctorConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorConsultation
        fields = [ "doctor_id","employee_id",  "consultation_for", "appointment_date", "appointment_time" ,'reason_for_consultation', "meeting_pref_type", "reports"]
      
class UpdateDoctorConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorConsultation
        fields = [ 'doctor_id',  'confirmed', 'transcript', 'next_appointment', 'appointment_date', 'appointment_time', 'reschedule_appointment', 'reason_for_reschedule', 'status', 'meeting_pref_type']

class ShowDoctorConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorConsultation
        fields = '__all__'
        depth = 2
        
        
class DoctorRescheduleConsultaionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorConsultation
        fields = [ 'reschedule_by', 'status', 'confirmed', 'reason_for_reschedule', 'reschedule_appointment', 'appointment_date', 'appointment_time', ]
    


class DoctorConsultationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorConsultationDetails
        fields = '__all__'


class ShowDoctorConsultationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorConsultationDetails
        fields = '__all__'
        depth  = 1
        

        # fields = [ "employee_id", "gender", "full_name", "relationship", "marital_status" , "age", "gender", "mobile_no"]
     
     

class UpdateDoctorConsultationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorConsultation
        fields = [ 'doctor_id', 'consultation_for', 'confirmed', 'transcript', 'next_appointment', 'appointment_date', 'appointment_time', 'reschedule_appointment', 'reason_for_reschedule', 'status', 'meeting_pref_type']

class DoctorPrescriptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorPrescriptions
        fields = '__all__'