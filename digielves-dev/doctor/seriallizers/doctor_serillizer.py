
from digielves_setup.models import DoctorAchivement, DoctorPersonalDetails,User
from rest_framework import serializers




# class UpdateDoctorPersonalDetailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model=DoctorPersonalDetails
#         fields = ['first_name','last_name','phone_no','speciality','license_no','year_of_experience','gender','language_spoken']

class DoctorPersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorPersonalDetails
        fields = ['user_id', 'firstname','lastname','phone_no','speciality','license_no','year_of_experience','gender','language_spoken','profile_picture']
        #depth=1  


class RegNdDoctorPersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorPersonalDetails
        fields = [ 'firstname','lastname','phone_no','speciality','license_no','year_of_experience','gender','language_spoken']
        
class ShowDoctorPersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorPersonalDetails
        fields = '__all__'
        
        
class UpdateDoctorPersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorPersonalDetails
        fields = [ 'firstname','lastname','phone_no','speciality','license_no','year_of_experience','gender','language_spoken']  


class DoctorAchivementSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorAchivement
        fields = ['user_id', 'achivement_title']

class UserRegistraionSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields = ['email','firstname','lastname','phone_no','user_role','user_type']