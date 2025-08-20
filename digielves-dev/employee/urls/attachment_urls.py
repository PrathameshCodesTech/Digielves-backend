
from django.urls import path
from employee.views.attachment import AttachmentViewSet


urlpatterns = [

    path(r'task/add-attachment/',AttachmentViewSet.as_view({'post':'createTaskAttachment'})),
    path(r'task/get-attachment/',AttachmentViewSet.as_view({'get':'getTaskAttachmentData'})),
    path(r'task/update-attachment/',AttachmentViewSet.as_view({'put':'updateTaskAttachment'})),
    path(r'task/delete-attachment/',AttachmentViewSet.as_view({'delete':'deleteTaskAttachment'}))
]