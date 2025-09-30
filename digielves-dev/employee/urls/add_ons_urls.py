from django.urls import path
from employee.views.add_ons import AddOnsMeetingNdTaskViewset



urlpatterns = [

    path(r'add-ons/get-data/',AddOnsMeetingNdTaskViewset.as_view({'get':'getAddOnsDetails'})),

]