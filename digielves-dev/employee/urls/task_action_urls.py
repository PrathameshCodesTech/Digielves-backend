from django.contrib import admin
from django.urls import path, include
from employee.views.checkList_task import TemplateTaskListViewSet
from employee.views.task_action import TaskActionViewSet
from employee.views.template_checklist import *


urlpatterns = [

    path(r'task/add-task-action/',TaskActionViewSet.as_view({'post':'createTaskAction'})),
    path(r'task/get-task-action/',TaskActionViewSet.as_view({'get':'getTaskWithActions'})),
]