# serializers.py
from rest_framework import serializers

from digielves_setup.models import EmployeePersonalDetails, OrganizationBranch, OrganizationDetails, User, UserCreation

class ExtOrganizationBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationBranch
        fields = '__all__'

class ExtOrganizationDetailsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = OrganizationDetails
        fields = '__all__'

class OrgUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'

class UserRegUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'
        
class EmployeeRegSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmployeePersonalDetails
        fields = '__all__'

class UserCreationRegSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserCreation
        fields = '__all__'