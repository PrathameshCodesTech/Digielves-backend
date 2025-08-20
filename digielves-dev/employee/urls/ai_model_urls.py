
from django.urls import path
from employee.views.ai_summery_model import AiViewSet



urlpatterns = [

    path(r'ai/get-summery/',AiViewSet.as_view({'post':'GetSummery'})),

]