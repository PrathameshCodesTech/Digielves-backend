from digielves_setup.models import BirthdayTemplates, Birthdays, EmployeePersonalDetails, OrganizationDetails, User
from rest_framework import serializers

class GetOrganizationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationDetails
        fields = [ 'name', 'support_mail','org_website_link']

class GetUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'firstname', 'lastname']

class GetUserDetailsSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()
    organization_id = serializers.SerializerMethodField()

    class Meta:
        model = EmployeePersonalDetails
        fields = ['firstname', 'lastname','employee_id', 'date_of_birth', 'phone_no', 'job_title', 'designation','department', 'profile_picture', 'user_id', 'organization_id']
        depth = 1

    def get_user_id(self, obj):
        try:
            user = obj.user_id
            return GetUserSerializer(user).data
        except Exception as e:
            return {}
    
    def get_organization_id(self, obj):
        try:
            user = obj.organization_id
            return GetOrganizationDetailsSerializer(user).data
        except Exception as e:
            return {}
        

class GetBdTemplateCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = BirthdayTemplates
        fields =['id','birthday','bdCard','card_name']
    

class GetUniqueBdTemplateCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = BirthdayTemplates
        # fields =['id','bdCard', 'bd_wish',]
        fields = '__all__'


class GetBdWithTempCardSerializer(serializers.ModelSerializer):
    user_id = GetUserSerializer()
    class Meta:
        model = BirthdayTemplates
        # fields =['id','bdCard', 'bd_wish',]
        fields = '__all__'
        depth = 1