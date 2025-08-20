from django.contrib import admin
from django.urls import path, include

from employee.views.task_checklist_task import TasksinTaskViewSet


from employee.views.template import *


urlpatterns = [

    path(r'task/checklist/create-task/',TasksinTaskViewSet.as_view({'post':'create_tasks_in_task'})),
    path(r'task/checklist/get-task/',TasksinTaskViewSet.as_view({'get':'get_task_in_tasks'})), # has to delete this
    path(r'task/checklist/task/get-task-assigned-users/',TasksinTaskViewSet.as_view({'get':'get_task_assigned_users'})),
    
    #path(r'task/checklist/update-assignto/',TasksinTaskViewSet.as_view({'put':'UpdateChecklistTaskAssignTo'})),
    path(r'task/sub_task/update-checklist-task/',TasksinTaskViewSet.as_view({'put':'updateChecklistUserTasks'})),
    path(r'task/checklist/task/trash/',TasksinTaskViewSet.as_view({'delete':'delete_checklistTaskData'})),
    path(r'task/checklist/task/get-task-unassigned-users/',TasksinTaskViewSet.as_view({'get':'get_unassigned_users_task_checklist_task'})),
    path(r'task/checklist/task/get-task-unassigned-custom-users/',TasksinTaskViewSet.as_view({'get':'get_unassigned_users_task_checklist_task_customBoard'})),
    
    path(r'task/get-subtask/',TasksinTaskViewSet.as_view({'get':'get_task_in_tasks'})), # new api
]