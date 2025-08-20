from rest_framework import serializers
from digielves_setup.models import EmployeePersonalDetails, User




class UserShowSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields = '__all__'

class UserRegistraionSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields = ['email','firstname','lastname','phone_no','user_role','user_type']
        
class UpdateUserRegistraionSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields = ['firstname','lastname','phone_no','user_role','user_type']


class UserForgetSeriallizer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['email', 'password','user_role',]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'firstname', 'lastname']


class GetPersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=EmployeePersonalDetails
        fields = ['firstname','lastname','designation','phone_no']