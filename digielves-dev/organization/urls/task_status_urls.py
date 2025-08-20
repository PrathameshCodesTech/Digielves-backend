from django.contrib import admin
from django.urls import path, include

from organization.views.task_status import TasksStatusViewSet







urlpatterns = [
    path(r'create_status/',TasksStatusViewSet.as_view({'post':'AddStatus'})),
    path(r'update_status_field/',TasksStatusViewSet.as_view({'put':'updateTasksStatusField'})),
    path(r'get_status_fields/',TasksStatusViewSet.as_view({'get':'getStatuses'})),
    path(r'delete_status/',TasksStatusViewSet.as_view({'delete':'deleteStatus'})),
    
    path(r'get_organization_tasks/',TasksStatusViewSet.as_view({'get':'get_org_task'})),
    


    
]