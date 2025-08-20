from digielves_setup.models import  EmployeePersonalDetails, OrganizationBranch, OrganizationDetails
from rest_framework import serializers





class organizationBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model=OrganizationBranch
        fields = '__all__'

class GetOrganizationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=OrganizationDetails
        fields = [ 'id','name']


class OrganizationBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationBranch
        fields = '__all__'

class OrganizationDetailsSerializer(serializers.ModelSerializer):
    branches = OrganizationBranchSerializer(many=True, read_only=True)

    class Meta:
        model = OrganizationDetails
        fields = '__all__'
        
        
class EmployeeSerializer(serializers.ModelSerializer):


    class Meta:
        model = EmployeePersonalDetails
        fields = ['firstname', 'lastname', 'user_id']