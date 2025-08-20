from django.urls import path

from employee.views.extension.slots import AddSlotsViewSet, ExtAvailableSlotsViewSet, CreateMeetingViewSet



urlpatterns = [

    # path(r'add_slots/',ExtAvailableSlotsViewSet.as_view({'post':'ExtAvailableSlotsListCreate'})),
    # path(r'get_slots/',ExtAvailableSlotsViewSet.as_view({'get':'get_available_slots'})),
    path(r'create_meeting/',CreateMeetingViewSet.as_view({'post':'createMeeting'})),
    path(r'available/confirm/',CreateMeetingViewSet.as_view({'get':'createMeetingGet'})),

    path(r'calender/get/',CreateMeetingViewSet.as_view({'get':'get_calender_extension'})),
    
    path(r'add_slots/',AddSlotsViewSet.as_view({'post':'add_extension_slots'})),
    path(r'get_slots/',AddSlotsViewSet.as_view({'get':'get_extension_slots'})),
    
    path(r'get_events/',CreateMeetingViewSet.as_view({'get':'get_extension_calender_reminder'})),
]