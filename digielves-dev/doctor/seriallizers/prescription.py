
from digielves_setup.models import DoctorPrescriptions 
from rest_framework import serializers




class ShowDoctorPrescriptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorPrescriptions
        fields = '__all__'
        
        
class DoctorPrescriptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorPrescriptions
        fields = '__all__'

    