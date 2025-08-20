from digielves_setup.models import User
from rest_framework import serializers



class OutsiderUserRegistraionSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields = ['email','firstname','lastname','phone_no','user_role','user_type']