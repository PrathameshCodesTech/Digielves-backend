from digielves_setup.models import OutsiderUser, ReportingRelationship, UserCreation,User
from rest_framework import serializers


class UserCreationSerializers(serializers.ModelSerializer):
    class Meta:
        model=UserCreation
        fields = '__all__'
        depth = 1
        

class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model=User
        fields = ['id','email','firstname','lastname','phone_no','active']

class UserCreationSerializersForUsers(serializers.ModelSerializer):
    employee_user_id=UserSerializers()
    class Meta:
        model=UserCreation
        fields = ['id','email','company_employee_id','employee_user_id']
        depth = 1

class UpdateUserCreationSerializers(serializers.ModelSerializer):
    class Meta:
        model=UserCreation
        fields = ['organization_id','created_by','email','company_employee_id','organization_location']      

class InviteUserCreationSerializers(serializers.ModelSerializer):
    class Meta:
        model=UserCreation
        fields = ['organization_id','created_by','email','company_employee_id'] 
        
class CreatingUserCreationSerializers(serializers.ModelSerializer):
    class Meta:
        model=UserCreation
  
        exclude = ["organization_id","token"] 
        
class SendEmailserializers(serializers.ModelSerializer):
    class Meta:
        model=UserCreation
        fields = ['id','email']    

class UserApprovedSerializers(serializers.ModelSerializer):
    class Meta:
        model=User
        fields = ['id','email','firstname','lastname','phone_no','active']

class ReportingUserCreationSerializers(serializers.ModelSerializer):
    class Meta:
        model=UserCreation
  
        fields = ["id","email"] 

class ReportingRelationshipApprovedSerializers(serializers.ModelSerializer):

    # reporting_user = ReportingUserCreationSerializers()
    reporting_to_user = ReportingUserCreationSerializers()

    class Meta:
        model = ReportingRelationship
        fields = ['reporting_to_user', 'hierarchy']


class UserCreationApprovedSerializers(serializers.ModelSerializer):
    employee_user_id = UserApprovedSerializers() 
    reporting_to = ReportingRelationshipApprovedSerializers(many=True, source='reporting_relationships')
    
    class Meta:
        model = UserCreation
        fields = ['id','employee_user_id', 'email', 'company_employee_id', 'processed', 'verified', 'reporting_to']


class GetRelationHierarchySerializers(serializers.ModelSerializer):

    reporting_user = ReportingUserCreationSerializers()
    reporting_to_user = ReportingUserCreationSerializers()

    class Meta:
        model = ReportingRelationship
        fields = ['id','reporting_user','reporting_to_user', 'hierarchy']


class GetHierarchySSerializers(serializers.ModelSerializer):
    reporting_to = GetRelationHierarchySerializers(many=True, source='reporting_relationships')
    
    class Meta:
        model = UserCreation
        fields = ['id','email', 'reporting_to']
        

class OutsiderUserSerializers(serializers.ModelSerializer):
    added_by = UserSerializers()
    approved_by = UserSerializers()
    approved_date = serializers.SerializerMethodField()
    invited_date = serializers.SerializerMethodField()
    firstname = serializers.SerializerMethodField()
    lastname = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()

    class Meta:
        model = OutsiderUser
        fields = ['id', 'email', 'added_by', 'approved_by' ,'processed', 'verified', 'approved_date', 'invited_date', 'firstname','lastname','phone_no']

    def get_approved_date(self, obj):
        if obj.approved_date:
            return obj.approved_date.isoformat()
        return None

    def get_invited_date(self, obj):
        if obj.invited_date:
            return obj.invited_date.isoformat()
        return None
    
    def get_firstname(self, obj):
        if obj.related_id:
            return obj.related_id.firstname 
        return None
    
    def get_lastname(self, obj):
        if obj.related_id:
            return obj.related_id.lastname
        return None
    def get_phone_no(self, obj):
        if obj.related_id:
            return obj.related_id.phone_no
        return None