from digielves_setup.models import SalesFollowUp, SalesLead, SalesStatus, TaskStatus, User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['firstname', 'lastname']
           


class CreateSalesLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesLead
        exclude = ['assign_to']
        
class updateSalesLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesLead
        fields = '__all__'


class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatus
        fields = ['id','status_name','color']

class UserSerializers(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id')
    class Meta:
        model = User
        fields = ['user_id','email','firstname','lastname']
class GetSalesLeadSerializer(serializers.ModelSerializer):
    created_by = UserSerializers()
    assign_to = UserSerializers(many =True)
    status = TaskStatusSerializer()
    
    class Meta:
        model = SalesLead
        exclude = ['inTrash','updated_at']
        # depth =1

class salesStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesStatus
        fields = ['id','status_name','fixed_state']
        

class SalesFollowupSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesFollowUp
        fields = ['user','sales_lead', 'followup_date', 'description']
        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'firstname', 'lastname']

class getSalesFollowupSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = SalesFollowUp
        fields = ['id', 'followup_date', 'description', 'user_id', 'name','notes']

    def get_name(self, obj):
        return f"{obj.user.firstname} {obj.user.lastname}"
        
