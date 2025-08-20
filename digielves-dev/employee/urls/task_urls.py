from django.contrib import admin
from django.urls import path, include

from employee.views.task import ChangeTaskStatusViewSet, TaskStatusNullDeleteViewSet, TaskStatusViewSet, TaskViewSet



urlpatterns = [

    # path(r'board/add-task/',TaskViewSet.as_view({'post':'create_task'})),
    path(r'add-task/',TaskViewSet.as_view({'post':'create_task_individual'})),
    path(r'task/update-assign-task/',TaskViewSet.as_view({'put':'UpdateTaskAssignTo'})),
    path(r'update-status-task/',TaskViewSet.as_view({'put':'changeIndividualTaskStatus'})),
    path(r'update-user-task/',TaskViewSet.as_view({'put':'updateUserTasks'})),
    path(r'get-task/',TaskViewSet.as_view({'get':'getUserTasks'})),
    path(r'my_board/get-task/',TaskViewSet.as_view({'get':'getUserTask_NotCheck'})),
    path(r'board/update-task/',TaskViewSet.as_view({'put':'updateTaskData'})),
    path(r'board/task/trash/',TaskViewSet.as_view({'delete':'deleteTaskData'})),
    path(r'board/get-task/',TaskViewSet.as_view({'get':'getTaskData'})),
    path(r'get-user-assigned-task/',TaskViewSet.as_view({'get':'getUserTasks'})),
    path(r'get-user-created-task/',TaskViewSet.as_view({'get':'getUserCreatedTasks'})),
    path(r'board/update-task-checklist/',TaskViewSet.as_view({'put':'update_task_checklist'})),
    path(r'task/get-action-and-chats/',TaskViewSet.as_view({'get':'get_task_actions_and_chats'})),

    path(r'task/get-user/',TaskViewSet.as_view({'get':'get_unassigned_users_task'})),
    path(r'task/get-task-assigned-users/',TaskViewSet.as_view({'get':'get_task_assigned_users'})),
    
    path(r'task/get-task-filtered/',TaskViewSet.as_view({'get':'getUserSpecificTasks'})),
    
    path(r'task/update-task/',ChangeTaskStatusViewSet.as_view({'put':'changeStatus'})),
    
    path(r'task/get-status/',TaskStatusViewSet.as_view({'get':'get_task_status'})),
    
    # not for prod
    path(r'task/delete_null_status/',TaskStatusNullDeleteViewSet.as_view({'delete':'delete_null_status'})),
    path(r'task/np/add_personal_status/',TaskStatusNullDeleteViewSet.as_view({'post':'add_personal_status'})),
    
]
