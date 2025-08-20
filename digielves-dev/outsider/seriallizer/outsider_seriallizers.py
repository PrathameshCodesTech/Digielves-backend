from digielves_setup.models import Board, Category, TaskStatus, Tasks, Template, User
from rest_framework import serializers



class OutsiderUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields = ['id','email','firstname','lastname','phone_no']
        
        
class OutsiderUserSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id')
    class Meta:
        model = User
        fields = ['user_id','email','firstname','lastname','phone_no']
        
class OutsidersGetBoardsSerializer(serializers.ModelSerializer):
    
    created_by = OutsiderUserSerializer() 
    assign_to = OutsiderUserSerializer(many = True)
    class Meta:
        model = Board
        fields = '__all__'
        
        
# get CustomBoard task
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name']
class TemplateSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    class Meta:
        model = Template
        fields = ['template_name','category']
class OutsidersUserSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id')
    class Meta:
        model = User
        fields = ['user_id','email','firstname','lastname','phone_no']
class OutsiderBoardSerializers(serializers.ModelSerializer):
    created_by = OutsidersUserSerializer()
    assign_to = OutsidersUserSerializer(many=True)
    template = TemplateSerializer()
    

    class Meta:
        model = Board
        fields = '__all__'


class OutsiderTaskSerializerForBoard(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = '__all__'
        
class OutsiderTaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatus
        fields = ['id','status_name','fixed_state']