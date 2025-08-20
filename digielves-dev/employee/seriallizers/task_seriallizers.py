from rest_framework import serializers
# from .models import Template
from digielves_setup.models import Checklist, SubTaskChild, SubTasks, TaskAction, TaskChatting, TaskChecklist, TaskStatus, Tasks, User, TaskHierarchy
from datetime import datetime, timezone
from django.db.models import Q


# class CustomDateTimeField(serializers.DateTimeField):
#     def to_representation(self, value):
#         # Convert the datetime to the desired timezone format
#         if value:
#             # Convert the datetime to UTC timezone
#             value = value.astimezone(timezone.utc)
#             # Format the datetime string as desired
#             formatted_datetime = value.strftime('%Y-%m-%d %H:%M:%S%z')
#             return formatted_datetime
#         return None
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        exclude = ['assign_to']
        # fields = '__all__'

        depth = 2

class mydayUserSerializers(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id')
    class Meta:
        model = User
        fields = ['user_id','email','firstname','lastname','phone_no']
class TaskGetSerializer(serializers.ModelSerializer):
    # due_date = CustomDateTimeField()
    assign_to = mydayUserSerializers(many = True)
    class Meta:
        model = Tasks
        exclude = ["due_date_exiting","due_date_latest_existing","inTrash","project_file_name","start_date","end_date"]
        # fields = '__all__'
        
        # depth = 2

class HierarchyTaskGetSerializer(serializers.ModelSerializer):
    # due_date = CustomDateTimeField()
    assign_to = mydayUserSerializers(many = True)
    class Meta:
        model = TaskHierarchy
        fields = '__all__'

class TaskIndividualSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        exclude = ['checklist']
class TaskSerializerForBoard(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = '__all__'
        
class TaskChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskChatting
        fields = '__all__'
        depth = 1

class TaskChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskChecklist
        fields = '__all__'
        
class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatus
        fields = ['id','status_name','color']

class UserSerializers(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id')
    class Meta:
        model = User
        fields = ['user_id','email','firstname','lastname','phone_no']
# for GetTasksChecklists
class GetTaskChecklistSerializer(serializers.ModelSerializer):
    status=TaskStatusSerializer()
    assign_to=UserSerializers(many=True)
    class Meta:
        model = TaskChecklist
        fields =['id','name','created_by','status','due_date','urgent_status','assign_to','created_at']
     

class GetTaskChecklistsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskChecklist
        fields =['id','Task','name','created_by','completed','created_at']



        
class GetChecklistTasksSerializer(serializers.ModelSerializer):
    status=TaskStatusSerializer()
    assign_to=UserSerializers(many=True)
    class Meta:
        model = SubTasks
        fields = '__all__'




class SubTaskChildSerializer(serializers.ModelSerializer):
    status=TaskStatusSerializer()
    assign_to=UserSerializers(many=True)
    created_by = UserSerializers()
    class Meta:
        model = SubTaskChild
        fields = '__all__'


class GetTask_subTaskSerializer(serializers.ModelSerializer):
    status=TaskStatusSerializer()
    assign_to=UserSerializers(many=True)
    created_by = UserSerializers()
    subtaskchild_set = serializers.SerializerMethodField()
    # due_date = CustomDateTimeField()
    class Meta:
        model = SubTasks
        fields = '__all__'

    def get_subtaskchild_set(self, obj):
        request = self.context.get('request')
        user_id = request.GET.get('user_id') if request else None
        print("-------------ahhaha")
        print(user_id)
        # Filter SubTaskChild objects where inTrash is False and assigned to the user or created by the user
        subtaskchildren = obj.subtaskchild_set.filter(
            Q(inTrash=False) & 
            (Q(assign_to=user_id) | Q(created_by__id=user_id) | 
             Q(subtasks__created_by__id=user_id) | Q(subtasks__assign_to__id=user_id) |
             Q(subtasks__Task__created_by__id=user_id) | Q(subtasks__Task__assign_to__id=user_id))
        ).distinct()
        return SubTaskChildSerializer(subtaskchildren, many=True).data

class TaskChecklistTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTasks
        fields = '__all__'   

class UpdateTaskChecklistTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTasks
        fields = '__all__'    

class TasksforchecklistSerializers(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = '__all__' 
        
class TaskActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAction
        fields = '__all__' 

class TaskActionChattingSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(read_only=True)
    task = serializers.PrimaryKeyRelatedField(read_only=True)
    remark = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    
class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatus
        fields = ['id','status_name','fixed_state', 'color']
        


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checklist
        fields = ['id', 'name']
        


class SubTaskGetSerializer(serializers.ModelSerializer):
    task_id = serializers.SerializerMethodField()
    which_task = serializers.SerializerMethodField()
    tag = serializers.SerializerMethodField()
    board_id = serializers.SerializerMethodField()
    is_personal = serializers.SerializerMethodField()
    
    class Meta:
        model = SubTasks
        exclude = ["due_date_existing","due_date_latest_existing","inTrash","start_date","end_date"]
        
    def get_task_id(self, obj):
        return obj.Task.id if obj.Task else None

    def get_which_task(self, obj):
        return "SubTask"
    

    def get_tag(self, obj):
        return "CustomBoard" if hasattr(obj.Task, 'checklist') and obj.Task.checklist else "MyBoard"
    
    def get_board_id(self, obj):
        if obj.Task and obj.Task.checklist and obj.Task.checklist.board:
            return obj.Task.checklist.board.id
        return None
    
    def get_is_personal(self, obj):
        return False
    

class SubTaskChildGetSerializer(serializers.ModelSerializer):
    task_id = serializers.SerializerMethodField()
    which_task = serializers.SerializerMethodField()
    tag = serializers.SerializerMethodField()
    board_id = serializers.SerializerMethodField()
    is_personal = serializers.SerializerMethodField()
    
    class Meta:
        model = SubTaskChild
        exclude = ["inTrash","start_date","end_date"]
        
    def get_task_id(self, obj):
        return obj.subtasks.Task.id if obj.subtasks.Task else None

    def get_which_task(self, obj):
        return "SubTaskChild"
    

    def get_tag(self, obj):
        return "CustomBoard" if hasattr(obj.subtasks.Task, 'checklist') and obj.subtasks.Task.checklist else "MyBoard"
    
    def get_board_id(self, obj):
        if obj.subtasks.Task and obj.subtasks.Task.checklist and obj.subtasks.Task.checklist.board:
            return obj.subtasks.Task.checklist.board.id
        return None
    
    def get_is_personal(self, obj):
        return False

