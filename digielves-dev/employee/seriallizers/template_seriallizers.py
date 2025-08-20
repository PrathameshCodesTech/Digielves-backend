from rest_framework import serializers
# from .models import Template
from digielves_setup.models import  Category, SavedTemplateChecklist, SavedTemplateTaskList, Template, TemplateAttachments, TemplateChecklist, TemplateTaskList


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = '__all__'
        

class TemplateCheckListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateChecklist
        fields = '__all__'
        

class TemplateCheckListTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateTaskList
        fields = '__all__'



class TemplateAttachmentsSerializers(serializers.ModelSerializer):
    class Meta:
        model = TemplateAttachments
        fields = '__all__'




class TemplateTaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateTaskList
        fields = ['id', 'task_name']

class TemplateChecklistSerializer(serializers.ModelSerializer):
    tasks = TemplateTaskListSerializer(source='templatetasklist_set', many=True)

    class Meta:
        model = TemplateChecklist
        fields = ['id', 'name', 'tasks']

class TemplateAttachmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateAttachments
        fields = '__all__'
        
        


# saved template
class SavedTemplateTaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedTemplateTaskList
        fields = ['id', 'task_name']

class SavedTemplateChecklistSerializer(serializers.ModelSerializer):
    tasks = SavedTemplateTaskListSerializer(source='saved_task', many=True)

    class Meta:
        model = SavedTemplateChecklist
        fields = ['id', 'name', 'tasks']