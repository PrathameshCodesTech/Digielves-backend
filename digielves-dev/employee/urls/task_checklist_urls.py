from django.contrib import admin
from django.urls import path, include
from employee.views.task_checklist import TaskChecklistViewSet


from employee.views.template import *


urlpatterns = [

    path(r'task/create-task-checklist/',TaskChecklistViewSet.as_view({'post':'create_task_checklist'})),
    path(r'task/get-task-checklist/',TaskChecklistViewSet.as_view({'get':'GetTasksChecklists'})),     #has to delete this api
    path(r'task/update-checklist-status/',TaskChecklistViewSet.as_view({'put':'updatTaskChecklist'})),
    path(r'task/update-checklist-fields/',TaskChecklistViewSet.as_view({'put':'updateChecklistFields'})),
    path(r'task/delete-checklist/',TaskChecklistViewSet.as_view({'delete':'delete_checklistData'})),
    path(r'task/checklist/trash/',TaskChecklistViewSet.as_view({'delete':'moveToTrash'})),
    
    
    path(r'task/get-task_checklists/',TaskChecklistViewSet.as_view({'get':'GetTaskChecklists'})), #new api
]