

from digielves_setup.models import TaskStatus
from rest_framework import serializers
from digielves_setup.models import SubTasks, EmployeePersonalDetails, OrganizationDetails, TaskChecklist, TaskHierarchy, TaskStatus, Tasks, User
from digielves_setup.models import SubTasks, EmployeePersonalDetails, TaskChecklist, TaskStatus, Tasks, User


class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatus
        fields = [
            'id', 'status_name', 'fixed_state',
            'color', 'order','created_at'
        ]










class UserRegistraionSerializerAdmin(serializers.ModelSerializer):
    
    class Meta:
        model=User
        fields = ['firstname','lastname']
    
class StatuserializerAdmin(serializers.ModelSerializer):
    
    class Meta:
        model=TaskStatus
        fields = ['status_name']
        

class TaskChecklistSerializer(serializers.ModelSerializer):
    created_by = UserRegistraionSerializerAdmin()
    status = StatuserializerAdmin()
    checklist_tasks = serializers.SerializerMethodField()

    class Meta:
        model = TaskChecklist
        fields = ['id', 'name', 'created_by', 'status', 'created_at', 'updated_at', 'checklist_tasks']

    def get_checklist_tasks(self, task_checklist):
        checklist_tasks = task_checklist.subtasks_set.all()
        checklist_tasks_serializer = ChecklistTasksSerializer(checklist_tasks, many=True)
        return checklist_tasks_serializer.data

class ChecklistTasksSerializer(serializers.ModelSerializer):
    created_by = UserRegistraionSerializerAdmin()
    assign_to = UserRegistraionSerializerAdmin(many=True)
    status = StatuserializerAdmin()

    class Meta:
        model = SubTasks
        fields = ['id', 'task_topic', 'due_date', 'task_description', 'urgent_status', 'completed', 'status', 'created_by', 'assign_to', 'created_at', 'updated_at']

class TasksSerializerOrganization(serializers.ModelSerializer):
    created_by = UserRegistraionSerializerAdmin()
    assign_to = UserRegistraionSerializerAdmin(many=True)
    organization_name = serializers.SerializerMethodField()
    status = StatuserializerAdmin()

    class Meta:
        model = TaskHierarchy
        fields = ['id', 'task_topic', 'due_date', 'task_description', 'urgent_status', 'reopened_count', 'organization_name', 'status', 'created_by', 'assign_to', 'created_at']

    def get_organization_name(self, task):
        try:
            employee_details = EmployeePersonalDetails.objects.get(user_id=task.created_by)
            organization_name = employee_details.organization_id.name if employee_details.organization_id else None
            return organization_name
        except EmployeePersonalDetails.DoesNotExist:
            return None
        except AttributeError:
            return None

    def get_sub_tasks(self, task):
        task_checklists = task.taskchecklist_set.all()
        sub_tasks = []
        for task_checklist in task_checklists:
            sub_tasks.extend(task_checklist.subtasks_set.all())

        sub_tasks_serializer = ChecklistTasksSerializer(sub_tasks, many=True)
        return sub_tasks_serializer.data

