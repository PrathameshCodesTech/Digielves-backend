from django.urls import path

from employee.views.calender.event import EventsViewset
from employee.views.calender.meeting import DashboardViewset, MeetingNdEventsndTaskViewset, MeetingViewset, ZoomViewset,meetSummeryViewset




urlpatterns = [

    path(r'calender/create-meeting/',MeetingViewset.as_view({'post':'createMeeting'})),
    path(r'calender/get-meeting/',MeetingViewset.as_view({'get':'getMeeting'})),
    path(r'calender/update-meeting-status/',MeetingViewset.as_view({'put':'update_meeting_status'})),
    path(r'calender/download-meeting-video/',MeetingViewset.as_view({'get':'download_meeting_video'})),

    path(r'calender/get-calender-events/',MeetingNdEventsndTaskViewset.as_view({'get':'getEventsAndMeetingsAndTask'})), # old api
    # path(r'calender/get-calender_events/',MeetingNdEventsndTaskViewset.as_view({'get':'get_user_calender_reminder'})), # new api
    path(r'calender/test-get-calenders-event/',MeetingNdEventsndTaskViewset.as_view({'get':'testgetEventsAndMeetingsAndTask'})),

    path(r'calender/update-calender-event/',MeetingNdEventsndTaskViewset.as_view({'put':'updateEventMeetingTask'})),
    path(r'calender/delete-calender-event/',MeetingNdEventsndTaskViewset.as_view({'delete':'delete_item'})),
    path(r'calender/get-event-nd-meeting/',DashboardViewset.as_view({'get':'getEventsAndMeetings'})),
    
    path(r'calender/meet/get_token/',ZoomViewset.as_view({'get':'get_zoom_access_token'})),
    path(r'calender/meet/create-zoom-meeting/',ZoomViewset.as_view({'post':'create_zoom_meeting'})),


    
    path(r'calender/meet/get-summery/',meetSummeryViewset.as_view({'get':'get_saved_summery_and_task'})),
    
    path(r'calender/meet/generate-summery/',MeetingViewset.as_view({'post':'generate_summery'})),
    
    

]