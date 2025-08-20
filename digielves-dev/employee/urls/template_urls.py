from django.contrib import admin
from django.urls import path, include

from employee.views.template import *


urlpatterns = [
    path(r'add-category/',TemplateViewSet.as_view({'post':'AddCategory'})),
    path(r'add-template/',TemplateViewSet.as_view({'post':'add_template_from_excel'})),
    path(r'add-template-checklist-from-excel/',TemplateViewSet.as_view({'post':'add_template_checklists_from_excel'})),
    path(r'add-checklist-task-from-excel/',TemplateViewSet.as_view({'post':'add_template_task_lists_from_excel'})),
    path(r'add-template/',TemplateViewSet.as_view({'post':'AddTemplate'})),
    path(r'get-template/',TemplateViewSet.as_view({'get':'template'})),
    path(r'update-template/',TemplateViewSet.as_view({'put':'updateTemplate'})),
    path(r'delete-template/',TemplateViewSet.as_view({'delete':'deleteTemplate'})),
    path(r'add-template-photo/',TemplateViewSet.as_view({'post':'add_template_attachment'})),
    path(r'update-template-photo/',TemplateViewSet.as_view({'put':'update_attachment'})),
    
    path(r'template/get_tasks/',GetTaskTemplateViewSet.as_view({'get':'get_template_details'}))
]