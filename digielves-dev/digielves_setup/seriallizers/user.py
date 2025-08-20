from rest_framework import serializers
from digielves_setup.models import User




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

class UserLoginSeriallizer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['email', 'password','user_role',]
        
class AddAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        exclude = ['password']