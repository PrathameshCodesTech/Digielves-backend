from rest_framework import serializers

from digielves_setup.models import Board, BoardPermission, Category, Checklist, Tasks, User, Template
from django.utils import timezone

class UserSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id')
    class Meta:
        model = User
        fields = ['user_id','email','firstname','lastname','phone_no']
        
class BoardSerializer(serializers.ModelSerializer):
    created_by = UserSerializer() 
    assign_to = UserSerializer(many = True)
    class Meta:
        model = Board
        exclude = ['updated_at']
        
class AddBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        exclude = ['assign_to']

        
        


class GetBoardsSerializer(serializers.ModelSerializer):
    
    created_by = UserSerializer() 
    assign_to = UserSerializer(many = True)
    class Meta:
        model = Board
        exclude = ['updated_at']
       

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name']
class TemplateSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    class Meta:
        model = Template
        fields = ['template_name','category']

class BoardSerializers(serializers.ModelSerializer):
    created_by = UserSerializer()
    assign_to = UserSerializer(many=True)
    template = TemplateSerializer()
    

    class Meta:
        model = Board
        fields = '__all__'
 
        #depth = 1

class BoardCheckListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checklist
        exclude = ['board']


class BoardCheckListForAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checklist
        fields = '__all__'

class BoardCheckListTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        exclude = ['assign_to','due_date']
        
        #fields = '__all__'
    
    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     # Convert due_datee to the local timezone
    #     data['due_datee'] = self.convert_to_timezone(instance.due_datee)
    #     print("---------------------------timezone")
    #     print(self.convert_to_timezone(instance.due_datee))
    #     return data

    # def convert_to_timezone(self, datetime_field):
    #     # Check if datetime_field exists and is not None
    #     if datetime_field:
    #         # Convert the datetime field to the local timezone
    #         return timezone.localtime(datetime_field).strftime('%Y-%m-%d %H:%M:%S')
    #     return None
    


class GetChecklistTasksSerializers(serializers.Serializer):
    id = serializers.IntegerField()
    task_topic = serializers.CharField(max_length=300, allow_blank=True, allow_null=True)
    due_date = serializers.CharField(max_length=200, allow_blank=True, allow_null=True)
    task_description = serializers.CharField(max_length=200, allow_blank=True, allow_null=True)
    urgent_status = serializers.BooleanField(default=False)
    completed = serializers.BooleanField(default=False)
    status = serializers.CharField(max_length=20, allow_blank=True, allow_null=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S.%f%z")
    updated_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S.%f%z")

    task_checklist = serializers.IntegerField()
    created_by = serializers.IntegerField()
    assign_to = serializers.ListField(child=serializers.IntegerField())
    


# Permission 
class OutsiderUserSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id')
    class Meta:
        model = User
        fields = ['user_id','email','firstname','lastname','phone_no']
class ChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checklist
        fields = ['id', 'name', 'sequence']

class BoardPermissionSerializer(serializers.ModelSerializer):
    checklist_permissions = ChecklistSerializer(many=True)
    access_to = OutsiderUserSerializer()

    class Meta:
        model = BoardPermission
        fields = ['user', 'access_to', 'board', 'can_view_board', 'can_view_checklists', 'checklist_permissions', 'created_at', 'updated_at']
        
class BoardPermissionGivenUsersSerializer(serializers.ModelSerializer):
    access_to = OutsiderUserSerializer()

    class Meta:
        model = BoardPermission
        fields = ['user', 'access_to']
        
class TaskBoardPermissionGivenUsersSerializer(serializers.ModelSerializer):
    access_to = OutsiderUserSerializer()

    class Meta:
        model = BoardPermission
        fields = ['user', 'access_to']