from django.contrib import admin
from django.urls import path, include

from employee.views.request import RequestViewSet






urlpatterns = [

    path(r'request/make_request/',RequestViewSet.as_view({'post':'make_request'})),
    path(r'request/get_requests/',RequestViewSet.as_view({'get':'get_requests'})),
    path(r'request/update_request/',RequestViewSet.as_view({'put':'update_request'})),
    path(r'request/delete_request/',RequestViewSet.as_view({'delete':'delete_request'})),


]