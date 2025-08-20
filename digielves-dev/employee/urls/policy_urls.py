from django.urls import path

from employee.views.policy.policy import PolicyViewSet



urlpatterns = [

    path(r'new/create/',PolicyViewSet.as_view({'post':'add_policy'})),
    path(r'new/get/',PolicyViewSet.as_view({'get':'get_policy'})),
    
]