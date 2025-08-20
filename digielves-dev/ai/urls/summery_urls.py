from django.urls import path

from ai.views.summery import AiViewSet
from ai.views.both_models import AiAudioAndTransriptViewSet






urlpatterns = [

    path(r'get-summery/',AiViewSet.as_view({'post':'GetSummery'})),
    path(r'get-doctor-summery/',AiViewSet.as_view({'post':'GetDoctorSummery'})),
    path(r'get-summery-from-pdf/',AiViewSet.as_view({'post':'GetSummery_from_pdf'})),
    
    path(r'get-audio-summery/',AiAudioAndTransriptViewSet.as_view({'post':'get_summery'})),
    
    

]