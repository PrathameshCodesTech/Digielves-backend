from django.contrib import admin
from django.urls import path, include

from organization.views.work_schedule import WorkScheduleViewSet







urlpatterns = [
    path(r'schedule/create/',WorkScheduleViewSet.as_view({'post':'create_schedule'})),
    path(r'schedule/get/',WorkScheduleViewSet.as_view({'get':'get_schedule'}))       
]