from rest_framework import serializers

from digielves_setup.models import TaskAttachments, Tasks

class Taskserializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = ['created_by']
class AttachmentSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(source='task.created_by', read_only=True)

    class Meta:
        model = TaskAttachments
        exclude = ('task',)  # Exclude the nested 'task' field from serialization

