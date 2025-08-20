from django.contrib import admin
from django.urls import path, include

from organization.views.organization_details import OrganizationDetailsClass, SubscriptionClass




urlpatterns = [

    path(r'add-details/',OrganizationDetailsClass.as_view({'post':'addOrganizationDetails'})),

    path(r'update-details/',OrganizationDetailsClass.as_view({'post':'updateOrganizationDetails'})),
    
    
    path(r'request_for_subscription/',SubscriptionClass.as_view({'post':'make_request_for_subscription'})),
    
    path(r'get_my_request/',SubscriptionClass.as_view({'get':'get_my_request'})),


]