
from django.contrib import admin
from django.urls import path, include

from doctor.view.calender import CalenderViewSet








urlpatterns = [


    path(r'calender/get-calender-details/',CalenderViewSet.as_view({'get':'get_calender_events'})),

]