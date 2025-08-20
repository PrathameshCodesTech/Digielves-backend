from digielves_setup.models import  SubTasks, TaskChecklist, Tasks, User
from rest_framework import serializers


class GetTrashedTasksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields =['id','created_by','checklist','task_topic','inTrash','status','due_date','created_at','updated_at']



class CombinedTaskTaskChecklistChecklistTaskSerializerOnly(serializers.Serializer):
    category = serializers.CharField(max_length=10)
    created_by = serializers.SerializerMethodField() 
    task_topic = serializers.CharField()
    due_date = serializers.CharField()  # Convert to string field
    inTrash = serializers.BooleanField()
    created_at = serializers.CharField()  # Convert to string field
    updated_at = serializers.CharField() 


    
    def to_representation(self, instance):

        if isinstance(instance, Tasks):
            data = {
                'category': 'Tasks',
                'id': instance.id,
                'created_by': instance.created_by.id,
                'task_topic': instance.task_topic,
                'due_date': str(instance.due_date),
                'inTrash' : instance.inTrash,
                'created_at': str(instance.created_at),
                'updated_at': str(instance.updated_at)
               
            }
        elif isinstance(instance, TaskChecklist):
            data = {
                'category': 'Task Checklist',
                'id': instance.id,
                'created_by': instance.created_by.id,
                'task_topic': instance.name,
                'due_date': "",
                'inTrash' : instance.inTrash,
                'created_at': str(instance.created_at),
                'updated_at': str(instance.updated_at)
            }
        elif isinstance(instance, SubTasks):
            data = {
                'category': 'Checklist Tasks',
                'id': instance.id,
                'created_by': instance.created_by.id,
                'task_topic': instance.task_topic,
                'due_date': str(instance.due_date),
                'inTrash' : instance.inTrash,
                'created_at': str(instance.created_at),
                'updated_at': str(instance.updated_at)
                
            }
    
        

        return data