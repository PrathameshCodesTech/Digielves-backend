
from digielves_setup.models import EmployeePersonalDetails
from rest_framework import serializers




class EmployeePersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=EmployeePersonalDetails
        exclude = ['profile_picture','organization_id','organization_location']
        
class EmployeePersonalDetailsConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model=EmployeePersonalDetails
        exclude = ['profile_picture']
        
        
class UpdateEmployeePersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=EmployeePersonalDetails
        fields = [ 'employee_id','firstname','lastname','date_of_birth','phone_no','job_title','department','designation','gender','work_location','profile_picture']  

