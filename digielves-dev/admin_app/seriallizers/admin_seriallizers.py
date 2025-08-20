from rest_framework import serializers
# from .models import Template
from digielves_setup.models import OrganizationDetails, DoctorPersonalDetails, OrganizationSubscriptionRequest, User, OrganizationBranch

class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id','active']

class UserSerializerForSpecific(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id','email','phone_no']
        
class UserSerializerForSpecificDoctor(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id','email']

class branchesSerializerForSpecific(serializers.ModelSerializer):
    
    class Meta:
        model = OrganizationBranch
        fields = "__all__"

class OrganizationDetailsSerializer(serializers.ModelSerializer):
    user_id = UserSerializer()
    class Meta:
        model = OrganizationDetails
        fields = '__all__'

class OrganizationSpecificDetailsSerializer(serializers.ModelSerializer):
    user_id = UserSerializerForSpecific()
    
    class Meta:
        model = OrganizationDetails
        fields = '__all__'
  
class OrganizationUpdateDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationDetails
        fields = '__all__'  

class DoctorDetailsSerializer(serializers.ModelSerializer):
    user_id = UserSerializer()
    class Meta:
        model = DoctorPersonalDetails
        fields = '__all__'      
        

class DoctorDpecificDetailsSerializer(serializers.ModelSerializer):
    user_id = UserSerializerForSpecificDoctor()
    class Meta:
        model = DoctorPersonalDetails
        fields = '__all__' 

class MYOrganizationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationDetails
        fields = ['name','support_mail']

class GetSubscriptionSerializer(serializers.ModelSerializer):
    organization = MYOrganizationDetailsSerializer()
    class Meta:
        model = OrganizationSubscriptionRequest
        fields = ['id','organization' ,'subscription_before','subscription_want','approved','approval_phase']

class OrganizationSerializer(serializers.ModelSerializer):
    user_id = UserSerializer()
    class Meta:
        model = OrganizationDetails
        fields = ['name','user_id']

