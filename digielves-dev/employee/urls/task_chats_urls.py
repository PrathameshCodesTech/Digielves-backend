from django.contrib import admin
from django.urls import path, include
from employee.views.checkList_task import TemplateTaskListViewSet
from employee.views.task_action import TaskActionViewSet
from employee.views.task_chats import TaskChatViewSet
from employee.views.template_checklist import *


urlpatterns = [

    path(r'task/add-message/',TaskChatViewSet.as_view({'post':'createTaskChatting'})),
    path(r'task/get-chats/',TaskChatViewSet.as_view({'get':'getTaskChats'})),

]