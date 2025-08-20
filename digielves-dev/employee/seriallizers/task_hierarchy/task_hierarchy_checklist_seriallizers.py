
from digielves_setup.models import TaskHierarchyChecklist
from rest_framework import serializers


class AddTaskHierarchyChecklistsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskHierarchyChecklist
        fields =['id','Task','name','created_by','completed','created_at']


class GetTaskHierarchyChecklistsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskHierarchyChecklist
        fields =['id','Task','name','created_by','completed','created_at']
