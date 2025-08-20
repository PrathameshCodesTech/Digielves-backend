from django.contrib import admin
from django.urls import path, include

from employee.views.task_comments import TaskCommentViewSet
from employee.views.template_checklist import *


urlpatterns = [

    path(r'task/add-comment/',TaskCommentViewSet.as_view({'post':'createTaskComment'})),
    path(r'task/get-comments/',TaskCommentViewSet.as_view({'get':'get_task_comments'})),
 
]