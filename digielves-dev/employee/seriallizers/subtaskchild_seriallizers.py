from digielves_setup.models import SubTaskChild, TaskStatus
from rest_framework import serializers


class CreateSubTaskChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTaskChild
        exclude = ['assign_to']


class TaskStatusForSubTaskChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatus
        fields = ["id","status_name", "fixed_state","color"]
class GetSubTaskChildSerializer(serializers.ModelSerializer):
    status = TaskStatusForSubTaskChildSerializer()
    class Meta:
        model = SubTaskChild
        fields = ['id','task_topic','due_date','subtasks','created_by', 'status']

        