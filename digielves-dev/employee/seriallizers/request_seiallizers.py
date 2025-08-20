from digielves_setup.models import DueRequest, User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id')
    class Meta:
        model = User
        fields = ['user_id','email','firstname','lastname','phone_no']
class GetRequestSerializer(serializers.ModelSerializer):
    board_id = serializers.SerializerMethodField()
    task_topic = serializers.SerializerMethodField()
    task_id = serializers.SerializerMethodField()
    sender = UserSerializer()
    request_from = serializers.SerializerMethodField()
    # parent_task_ids = serializers.SerializerMethodField()
    
    class Meta:
        model = DueRequest
        exclude  = ['created_at', 'updated_at','receiver'] 
    
    
    def get_board_id(self, obj):
        if obj.task and obj.task.checklist and obj.task.checklist.board:
            return obj.task.checklist.board.id
        return None
    
    def get_task_topic(self, obj):
        if obj.task:
            return obj.task.task_topic
        if obj.subtasks:
            return obj.subtasks.task_topic
        if obj.subtaskchild:
            return obj.subtaskchild.task_topic
        return None
    
    def get_task_id(self, obj):
        if obj.task:
            return obj.task.id
        if obj.subtasks:
            return obj.subtasks.id
        if obj.subtaskchild:
            return obj.subtaskchild.id
        return None
    
    def get_request_from(self, obj):
        if obj.task:
            return "task"
        if obj.subtasks:
            return "subtask"
        if obj.subtaskchild:
            return "subtaskchild"
        return None
    
    def get_parent_task_ids(self, obj):
        if obj.task:
            return {
                "task_id": obj.task.id,
                "subtask_id": None,
                "subtaskchild_id": None
            }
        if obj.subtasks:
            return {
                "task_id": obj.subtasks.Task.id,
                "subtask_id": obj.subtasks.id,
                "subtaskchild_id": None
            }
        if obj.subtaskchild:
            return {
                "task_id": obj.subtaskchild.subtasks.Task.id,
                "subtask_id": obj.subtaskchild.subtasks.id,
                "subtaskchild_id": obj.subtaskchild.id
            }
        return {
            "task_id": None,
            "subtask_id": None,
            "subtaskchild_id": None
        }
    
    # def get_task(self, obj):
    #     if obj.task:
    #         return obj.task.id
    #     if obj.subtasks:
    #         return obj.subtasks.Task.id
    #     if obj.subtaskchild:
    #         return obj.subtaskchild.subtasks.Task.id
    #     return None
    
    # def get_subtasks(self, obj):
    #     if obj.task:
    #         return obj.task.id
    #     if obj.subtasks:
    #         return obj.subtasks.id
    #     if obj.subtaskchild:
    #         return obj.subtaskchild.subtasks.Task.id
    #     return None


        