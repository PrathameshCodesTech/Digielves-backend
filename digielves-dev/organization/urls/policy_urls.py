from django.urls import path

from organization.views.policy import RequestPolicyViewSet




urlpatterns = [

    path(r'get_request/',RequestPolicyViewSet.as_view({'get':'get_requested_policy'})),
    
]