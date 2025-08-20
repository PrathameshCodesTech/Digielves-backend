
from pipes import Template
from digielves_setup.models import Board, Category, EmployeePersonalDetails, Meettings, TaskHierarchy, TaskHierarchyAttachments, TaskHierarchyDueRequest, TaskStatus, User
from rest_framework import serializers
from datetime import datetime, time
class CreateTaskHierarchySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskHierarchy
        exclude = ['assign_to','due_date', 'depend_on']
        

class GetTaskHierarchySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskHierarchy
        fields = '__all__'
        
        

# task in task
class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatus
        fields = ['id','status_name','color']

class UserSerializers(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id')
    class Meta:
        model = User
        fields = ['user_id','email','firstname','lastname','phone_no']
        
class TaskHierarchyChildrenSerializer(serializers.ModelSerializer):
    status = TaskStatusSerializer()
    assign_to = UserSerializers(many=True)
    created_by = UserSerializers()
    relevant = serializers.SerializerMethodField()
    class Meta:
        model = TaskHierarchy
        exclude = ['created_at', 'updated_at', 'sequence', 'inTrash','project_file_name', 'checklist']
        
    def get_relevant(self, obj):
        relevant_task_ids = self.context.get('relevant_task_ids', set())
        return obj.id in relevant_task_ids


# class GetTaskSubTaskSerializer(serializers.ModelSerializer):
#     status = TaskStatusSerializer()
#     assign_to = UserSerializers(many=True)
#     created_by = UserSerializers()
#     subtasks = serializers.SerializerMethodField()

#     class Meta:
#         model = TaskHierarchy
#         fields = '__all__'

#     def get_subtasks(self, obj):
#         request = self.context.get('request')
#         user_id = request.GET.get('user_id') if request else None

#         subtasks = obj.subtask_set.filter(
#             Q(inTrash=False) &
#             (Q(assign_to=user_id) | Q(created_by=user_id) |
#              Q(parent__created_by=user_id) | Q(parent__assign_to=user_id))
#         ).distinct()

#         return SubTaskChildSerializer(subtasks, many=True).data


class mydayUserSerializers(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id')
    profile_picture = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['user_id','email','firstname','lastname','phone_no','profile_picture']
        
    def get_profile_picture(self, obj):
        try:
            employee_details = EmployeePersonalDetails.objects.get(user_id=obj.id)
            return employee_details.profile_picture
        except EmployeePersonalDetails.DoesNotExist:
            return None
class MyDayTaskHierarchyGetSerializer(serializers.ModelSerializer):
    # due_date = CustomDateTimeField()
    assign_to = mydayUserSerializers(many = True)
    
    class Meta:
        model = TaskHierarchy
        exclude = ["inTrash","project_file_name","start_date","end_date", "status_changed_by_user", "status_changed_to_complete"]





class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name']

class TemplateSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    class Meta:
        model = Template
        fields = ['template_name','category']
class InTaskHierarchyBoardSerializers(serializers.ModelSerializer):
    created_by = mydayUserSerializers()
    assign_to = mydayUserSerializers(many=True)
    

    class Meta:
        model = Board
        fields = '__all__'
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.template:
            representation['template_name'] = instance.template.template_name
            if instance.template.category:
                representation['category_name'] = instance.template.category.name
                representation['category_id'] = instance.template.category.id
        return representation
        
class CustomBoardTaskHierarchyGetSerializer(serializers.ModelSerializer):
    # due_date = CustomDateTimeField()
    assign_to = mydayUserSerializers(many = True)
    class Meta:
        model = TaskHierarchy
        exclude = ["inTrash","project_file_name", "status_changed_by_user", "status_changed_to_complete"]

class GetBoardsInHierarchySerializer(serializers.ModelSerializer):
    
    created_by = mydayUserSerializers() 
    assign_to = mydayUserSerializers(many = True)
    class Meta:
        model = Board
        exclude = ['updated_at']





# attachment
class TaskHierarchyAttachmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = TaskHierarchyAttachments
        fields = "__all__"
        

# task trash

class CombinedTaskHierarchySerializer(serializers.Serializer):
    category = serializers.CharField(max_length=10)
    created_by = serializers.SerializerMethodField() 
    task_topic = serializers.CharField()
    due_date = serializers.CharField()  # Convert to string field
    inTrash = serializers.BooleanField()
    created_at = serializers.CharField()  # Convert to string field
    updated_at = serializers.CharField() 


    
    def to_representation(self, instance):

        if isinstance(instance, TaskHierarchy):
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
    
        

        return data
    
# due date change request

class GetDueDateRequestSerializer(serializers.ModelSerializer):
    board_id = serializers.SerializerMethodField()
    task_topic = serializers.SerializerMethodField()
    sender = mydayUserSerializers()
    request_from = serializers.SerializerMethodField()
    parent_task_ids = serializers.SerializerMethodField()

    class Meta:
        model = TaskHierarchyDueRequest
        exclude = ['created_at', 'updated_at', 'receiver']

    def get_board_id(self, obj):
        task = obj.task
        main_parent = get_main_parent_task(task)

        if task.checklist and task.checklist.board:
            return task.checklist.board.id
        elif main_parent and main_parent.checklist and main_parent.checklist.board:
            return main_parent.checklist.board.id

        return None

    def get_task_topic(self, obj):
        return obj.task.task_topic if obj.task else None

    def get_request_from(self, obj):
        return "subtask" if obj.task and obj.task.parent else "task"

    def get_parent_task_ids(self, obj):
        main_parent_id = get_main_parent_task(obj.task)
        return {"task_id": main_parent_id.id if main_parent_id else None}


def get_main_parent_task(task):
    """
    Given a task, return the main parent task if the task is a sub-level task, or None if the task is a main parent.
    """
    try:
        main_task = task
        while main_task.parent is not None:
            main_task = main_task.parent

        return main_task if main_task.id != task.id else None
    except TaskHierarchy.DoesNotExist:
        return None


# customize task and meeting
class MeettingsCustomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meettings
        fields = [
            'id', 'user_id', 'participant', 'other_participant_email', 'category', 
            'meet_link', 'meet_id', 'uuid', 'title', 'purpose', 'from_date', 
            'from_time', 'to_date', 'to_time', 'status_complete', 'meet_start_time',  'created_at', 'updated_at'
        ]

class TaskHierarchyCustomSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskHierarchy
        fields = [
            'id', 'created_by', 'assign_to',  'task_topic', 'due_date', 
            'task_description', 'urgent_status', 'status','start_date', 'end_date',  'created_at', 
            'updated_at'
        ]
        
        


class CombinedTaskMeetingSerializer(serializers.Serializer):

    
    def get_created_by(self, obj):
        if hasattr(obj, 'created_by'):
            return {
                "id": obj.created_by.id,
                "email": obj.created_by.email,
                "firstname": obj.created_by.firstname,
                "lastname": obj.created_by.lastname,
            }
        elif hasattr(obj, 'user_id'):
            try:
                return {
                    "id": obj.user_id.id,
                    "email": obj.user_id.email,
                    "firstname": obj.user_id.firstname,
                    "lastname": obj.user_id.lastname,
                }
            except:
                return {
                    "id": obj.user.id,
                    "email": obj.user.email,
                    "firstname": obj.user.firstname,
                    "lastname": obj.user.lastname,
                }
                
        elif hasattr(obj, 'employee_id'):
            return {
                "id": obj.employee_id.id,
                "email": obj.employee_id.email,
                "firstname": obj.employee_id.firstname,
                "lastname": obj.employee_id.lastname,
            }
        else:
            print(f"Object has no valid 'created_by' field: {obj}")
            return {
                "id": None,
                "email": None,
                "firstname": None,
                "lastname": None,
            }
            
    def get_status(self, obj):
        if obj.status:
            return {
                "id": obj.status.id,
                "status_name": obj.status.status_name,
                "color":obj.status.color
            }
        return None
    
    def get_assign_to(self, obj):
        return [
            {
                "id": user.id,
                "email": user.email,
                "firstname": user.firstname,
                "lastname": user.lastname,
            } for user in obj.assign_to.all()
        ]
    
    def get_participant(self, obj):
        return [
            {
                "id": user.id,
                "email": user.email,
                "firstname": user.firstname,
                "lastname": user.lastname,
            } for user in obj.participant.all()
        ]

    
    def to_representation(self, instance):
    
        if isinstance(instance, Meettings):
            
            data = {
                'category': 'Meeting',
                'id': instance.id,
                'title': instance.title,
                'from_datetime' : datetime.combine(instance.from_date, instance.from_time or time(0, 0)) if instance.from_date else "",
                'to_datetime': datetime.combine(instance.to_date, instance.to_time or time(0, 0)) if instance.to_date and instance.to_time else "", 
            
                'meet_link': instance.meet_link,
                'uuid': instance.uuid,
                'meet_id': instance.meet_id,
                'description': instance.purpose,
                'status_complete':instance.status_complete,
                'participant_ids': self.get_participant(instance),
                'other_participant_email': instance.other_participant_email,
                'created_by': self.get_created_by(instance)
            }
        elif isinstance(instance, TaskHierarchy):
            data = {
                'category': 'Task',
                'id': instance.id,
                'title': instance.task_topic,
                'from_datetime' : instance.due_date,
                'to_datetime' : instance.due_date,
                'created_by': self.get_created_by(instance),
                'description':instance.task_description,
                'urgent_status':instance.urgent_status,
                'status':self.get_status(instance),
                'reopened_count':instance.reopened_count,
                'start_date': instance.start_date,
                'end_date':instance.end_date,
                'assign_to':self.get_assign_to(instance)
            }
            
        return data