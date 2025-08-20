
from django.urls import path

from employee.views.work_schedule import UserWorkScheduleViewSet



urlpatterns = [

    path(r'work_schedule/create-schedule/',UserWorkScheduleViewSet.as_view({'post':'add_user_work_schedule'})),
    path(r'work_schedule/get-schedule/',UserWorkScheduleViewSet.as_view({'get':'get_user_work_schedule'})),
    
    path(r'work_schedule/slot/freeze/',UserWorkScheduleViewSet.as_view({'put':'update_user_work_slot'})),
    
    
]