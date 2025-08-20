from django.urls import path

from employee.views.calender.event import EventsViewset




urlpatterns = [

    path(r'calender/create-event/',EventsViewset.as_view({'post':'addEvent'})),

]