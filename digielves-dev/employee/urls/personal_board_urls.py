from django.contrib import admin
from django.urls import path, include

from employee.views.personal_board.personal_board import PersonalTaskViewSet




urlpatterns = [

    path(r'task/personal/create-task/',PersonalTaskViewSet.as_view({'post':'personal_create_task'})),
    path(r'task/personal/get-task/',PersonalTaskViewSet.as_view({'get':'personal_get_task'})),
    path(r'task/personal/get-attachment/',PersonalTaskViewSet.as_view({'get':'get_personal_task_attachment_data'})),
    path(r'task/personal/add-attachment/',PersonalTaskViewSet.as_view({'post':'create_personal_TaskAttachment'})),
    path(r'task/personal/delete-attachment/',PersonalTaskViewSet.as_view({'delete':'delete_personal_task_attachment'})),
    path(r'task/personal/update-task/',PersonalTaskViewSet.as_view({'put':'personal_task_update'})),
    path(r'task/personal/delete-task/',PersonalTaskViewSet.as_view({'delete':'personal_task_delete'})),

    path(r'task/personal/get-status/',PersonalTaskViewSet.as_view({'get':'get_personal_statuses'})),

]