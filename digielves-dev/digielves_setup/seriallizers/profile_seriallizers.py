from digielves_setup.models import Address, DoctorPersonalDetails, EmployeePersonalDetails, OrganizationDetails, User
from rest_framework import serializers


# ... Address, EmployeePersonalDetails serializers ...

class DoctorPersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorPersonalDetails
        fields = '__all__'

class OrganizationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationDetails
        fields = [ 'name', 'support_mail']



        
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email']

class EmployeePersonalDetailsSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()
    organization_id = serializers.SerializerMethodField()

    class Meta:
        model = EmployeePersonalDetails
        fields = ['firstname', 'lastname','employee_id', 'date_of_birth', 'phone_no', 'job_title', 'department', 'profile_picture', 'user_id', 'organization_id']
        depth = 1

    def get_user_id(self, obj):
        try:
            user = obj.user_id
            return UserSerializer(user).data
        except Exception as e:
            return {}
    
    def get_organization_id(self, obj):
        try:
            user = obj.organization_id
            return OrganizationDetailsSerializer(user).data
        except Exception as e:
            return {}
    



class UserUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone_no = serializers.CharField(max_length=10, required=False)
    date_of_birth = serializers.CharField(max_length=20, required=False)
