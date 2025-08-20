from django.contrib import admin
from django.urls import path, include
from employee.views.bg_image import BgImageViewSet

from organization.views.task_status import TasksStatusViewSet







urlpatterns = [
    path(r'add_bg_image/',BgImageViewSet.as_view({'post':'add_bg_image'})),
    path(r'get_bg_image/',BgImageViewSet.as_view({'get':'get_bg_image'}))


]