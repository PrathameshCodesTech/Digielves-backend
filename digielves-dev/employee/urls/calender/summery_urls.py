from django.urls import path

from employee.views.calender.summery import SummeryAiViewSet





urlpatterns = [

    path(r'calender/get-summery/',SummeryAiViewSet.as_view({'post':'GetSummery'})),
    path(r'calender/get-summery-and-task/',SummeryAiViewSet.as_view({'get':'get_summery_nd_task'})),
]