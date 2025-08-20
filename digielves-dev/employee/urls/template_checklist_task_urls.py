from django.contrib import admin
from django.urls import path, include
from employee.views.checkList_task import TemplateTaskListViewSet
from employee.views.template_checklist import *


urlpatterns = [

    path(r'add-checklist-task/',TemplateTaskListViewSet.as_view({'post':'CreateTask'})),
    path(r'get-checklist-task/',TemplateTaskListViewSet.as_view({'get':'getCheckListTaskData'})),
    
    path(r'update-checklist-task/',TemplateTaskListViewSet.as_view({'put':'updateTask'})),
    path(r'delete-checklist-task/',TemplateTaskListViewSet.as_view({'delete':'deleteTaskData'})),
]