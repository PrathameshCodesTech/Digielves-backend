from django.urls import path

from employee.views.task_hierarchy.task_checklist import TaskHierarchyChecklistViewSet






urlpatterns = [

    path(r'task/create-checklist/',TaskHierarchyChecklistViewSet.as_view({'post':'create_task_checklist'})),
    path(r'task/get-checklist/',TaskHierarchyChecklistViewSet.as_view({'get':'get_task_hierarchy_checklists'})),
    path(r'task/update-checklist/',TaskHierarchyChecklistViewSet.as_view({'put':'update_checklist_fields'})),
    path(r'task/delete-checklist/',TaskHierarchyChecklistViewSet.as_view({'delete':'delete_checklistData'})),
]