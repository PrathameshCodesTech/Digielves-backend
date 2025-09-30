
from digielves_setup.models import DoctorConsultation ,DoctorSlot, DoctorConsultationDetails
from rest_framework import serializers



class DoctorSlotCalenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSlot
        fields = ['slots','meeting_mode']

class DoctorConsultationDetailsCalenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorConsultationDetails
        fields = ['full_name']

class calenderDoctorConsultationseriallizers(serializers.ModelSerializer):
    doctor_slot = DoctorSlotCalenderSerializer()
    consultation_for=DoctorConsultationDetailsCalenderSerializer()
    class Meta:
        model=DoctorConsultation
        fields = ['id','appointment_date','consultation_for','doctor_slot']

        
        

        
        