from digielves_setup.models import EmployeePersonalDetails, Birthdays
from rest_framework import serializers


class EmployeePersonalDetailsforBirthdaySerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user_id.email', read_only=True)
    
    class Meta:
        model = EmployeePersonalDetails
        fields = ['firstname','lastname','date_of_birth','profile_picture','phone_no','email']


class BirthdaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Birthdays
        fields = ['id','firstname','lastname','date_of_birth','profile_picture','phone_no','email']

class UpdateBirthdaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Birthdays
        fields = ['user_id','firstname','lastname','date_of_birth','phone_no','email']
        
class AddBirthdaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Birthdays
        fields = ['user_id','firstname','lastname','date_of_birth','phone_no','email']