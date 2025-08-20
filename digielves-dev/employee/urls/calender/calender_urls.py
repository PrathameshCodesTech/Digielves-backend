from django.urls import path

from employee.views.calender.calender import CalenderViewSet



urlpatterns = [

    path(r'calender/get-near_date/',CalenderViewSet.as_view({'get':'get_available_slots'})),
    path(r'calender/get-due_task/',CalenderViewSet.as_view({'get':'get_due_task'})),
    path(r'calender/reschedule_event/',CalenderViewSet.as_view({'post':'reschedule_event'})),
    path(r'calender/get-specific_event/',CalenderViewSet.as_view({'get':'get_category_wise_calender_reminder'})),
    
    path(r'calender/get-events/',CalenderViewSet.as_view({'get':'get_all_events'})),
    path(r'calender/get-due_tasks/',CalenderViewSet.as_view({'get':'get_dued_task'})),
    path(r'calender/re_schedule_event/',CalenderViewSet.as_view({'post':'re_schedule_event'})),
    path(r'calender/get-fetch_event/',CalenderViewSet.as_view({'get':'get_category_wise_event'})),
    path(r'calender/update_event/',CalenderViewSet.as_view({'put':'update_events'})),
]