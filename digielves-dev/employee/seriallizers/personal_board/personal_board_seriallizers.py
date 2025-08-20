from rest_framework import serializers
# from .models import Template
from digielves_setup.models import  PersonalStatus, PersonalTask, PersonalTaskAttachments

class PersonalTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalTask
        fields = '__all__'

class PersonalStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalStatus
        fields = '__all__'
        
class ImportsPersonalStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalStatus
        fields = ["id","status_name", "fixed_state","color"]
        
class GetPersonalTaskSerializer(serializers.ModelSerializer):
    status = ImportsPersonalStatusSerializer()
    id = serializers.SerializerMethodField()  # Custom field for ID

    class Meta:
        model = PersonalTask
        fields = ['id', 'status', 'task_topic', 'due_date', 'task_description', 'urgent_status',
                  'completed', 'sequence',  'reopened_count', 'inTrash', 'created_at', 'updated_at', 'user_id']

    def get_id(self, obj):
        """Return the ID with the prefix 't_'."""
        return f"t_{obj.id}"
        
    
class GetPersonalTaskOnMyDaySerializer(serializers.ModelSerializer):
    checklist = serializers.SerializerMethodField() 
    assign_to = serializers.SerializerMethodField()

    class Meta:
        model = PersonalTask
        fields = ['id', 'task_topic', 'due_date', 'task_description', 'urgent_status',
                  'completed', 'sequence','is_personal', 'reopened_count', 'inTrash','created_at','updated_at' ,'checklist','status', 'user_id', 'assign_to']

    def get_checklist(self, obj):
        return getattr(obj, 'checklist', None)
    
    def get_assign_to(self, obj):
        return getattr(obj, 'assign_to', [])
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['created_by'] = representation.pop('user_id')
        return representation

class PersonalTaskAttachmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = PersonalTaskAttachments
        exclude = ('personaltask_id',) 
        

class GetPersonalStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalStatus
        fields = ['id','status_name','user_id']