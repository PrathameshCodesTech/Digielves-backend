
from django.urls import path

from admin_app.views.task_view import AdminTaskViewSet, OrgViewSet
from admin_app.views.task_view import AdminTaskViewSet






urlpatterns = [

    path(r'get_task-excel/',AdminTaskViewSet.as_view({'get':'get_task_excel'})),
    path(r'get_task/',AdminTaskViewSet.as_view({'get':'get_task'})),
    path(r'get_organization/',OrgViewSet.as_view({'get':'get_organizations'})),

] 