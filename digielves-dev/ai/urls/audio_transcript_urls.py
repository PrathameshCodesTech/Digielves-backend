from django.urls import path
from ai.views.audio_to_transcript import AiTransriptViewSet

from ai.views.summery import AiViewSet






urlpatterns = [

    path(r'get-transript/',AiTransriptViewSet.as_view({'post':'get_transcript'})),
    path(r'get-transript-small/',AiTransriptViewSet.as_view({'post':'get_transcript_small'})),
    path(r'get-transript-medium/',AiTransriptViewSet.as_view({'post':'get_transcript_medium'})),

]