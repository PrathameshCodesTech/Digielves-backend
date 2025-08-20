from django.urls import path

from employee.views.calender.event import EventsViewset
from employee.views.calender.teamsMeeting import teamsViewset



urlpatterns = [

    path(r'calender/create-teams-meeting/',teamsViewset.as_view({'post':'createTeamMeeting'})),

]