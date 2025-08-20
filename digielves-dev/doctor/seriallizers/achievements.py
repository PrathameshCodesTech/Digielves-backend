
from digielves_setup.models import DoctorAchivement, DoctorPersonalDetails
from rest_framework import serializers




class DoctorAchivementSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorAchivement
        fields = '__all__'
        
        
class AddDoctorAchivementSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorAchivement
        fields = [ 'achivement_title','user_id']  
