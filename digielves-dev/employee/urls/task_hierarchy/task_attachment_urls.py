from django.urls import path

from employee.views.task_hierarchy.task_attachment import TaskHierarchyAttachmentViewSet


urlpatterns = [

    path(r'task/add-attachment/',TaskHierarchyAttachmentViewSet.as_view({'post':'create_task_attachment'})),
    path(r'task/get-attachment/',TaskHierarchyAttachmentViewSet.as_view({'get':'get_task_attachments'})),
    path(r'task/delete-attachment/',TaskHierarchyAttachmentViewSet.as_view({'delete':'delete_task_attachment'}))
]