
from digielves_setup.models import DoctorSlot
from rest_framework import serializers





class DoctorSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorSlot
        fields = '__all__'

class GetDoctorSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorSlot
        fields = ['id','slots']