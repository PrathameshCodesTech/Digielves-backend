from django.contrib import admin
from django.urls import path, include
from employee.views.template_checklist import *


urlpatterns = [

    path(r'add-template-checklist/',TemplateChecklistViewSet.as_view({'post':'create'})),
    path(r'get-template-checklist/',TemplateChecklistViewSet.as_view({'get':'getChecklistData'})),
    path(r'update-template-checklist/',TemplateChecklistViewSet.as_view({'put':'updateChecklistData'})),
    path(r'delete-template-checklist/',TemplateChecklistViewSet.as_view({'delete':'deleteChecklistData'})),
]