from digielves_setup.models import UserCreation
from rest_framework import serializers


class UserCreationSerializers(serializers.ModelSerializer):
    class Meta:
        model=UserCreation
        fields = '__all__'
        # depth = 1


class UpdateUserCreationSerializers(serializers.ModelSerializer):
    class Meta:
        model=UserCreation
        fields = ['organization_id','created_by','email','company_employee_id']      
