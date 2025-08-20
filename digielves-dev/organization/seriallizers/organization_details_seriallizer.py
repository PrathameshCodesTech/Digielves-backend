

from digielves_setup.models import OrganizationDetails, OrganizationSubscriptionRequest
from rest_framework import serializers





class organizationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=OrganizationDetails
        #fields = '__all__'
        exclude = ["user_id"]
        
        
        
class UpdateOrganizationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=OrganizationDetails
        fields = [ 'name','support_mail','number_of_employee','number_of_subscription','organization_code','org_description','org_website_link']
        

class GetMySubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrganizationSubscriptionRequest
        fields = ['id' ,'subscription_before','subscription_want','approved','approval_phase']
