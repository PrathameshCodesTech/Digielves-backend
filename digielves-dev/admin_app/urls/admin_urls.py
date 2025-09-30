
from django.contrib import admin
from django.urls import path, include

from admin_app.views.admin_view import OrganizationDetailsViewSet, DoctorDetailsViewSet, OrganizationSubscriptionRequestViewSet

urlpatterns = [

    path(r'organization/get-organizations/',OrganizationDetailsViewSet.as_view({'get':'getOrganizations'})),
    path(r'organization/get-organization/',OrganizationDetailsViewSet.as_view({'get':'getspecificOrganizationDetails'})),
    path(r'organization/delete-organizations/',OrganizationDetailsViewSet.as_view({'delete':'deleteOrganization'})),
    path(r'organization/update-organizations/',OrganizationDetailsViewSet.as_view({'put':''})),
    
    path(r'doctor/get-doctors/',DoctorDetailsViewSet.as_view({'get':'getDoctors'})),
    path(r'doctor/get-doctor/',DoctorDetailsViewSet.as_view({'get':'getspecificDoctorDetails'})),
    path(r'doctor/delete-doctors/',DoctorDetailsViewSet.as_view({'delete':'deleteDoctor'})),
    
    path(r'subscription/get_requests/',OrganizationSubscriptionRequestViewSet.as_view({'get':'get_request'})),
    path(r'subscription/request/',OrganizationSubscriptionRequestViewSet.as_view({'put':'manage_request'})),
    
    path(r'organization/get_organizations_names/',OrganizationDetailsViewSet.as_view({'get':'getOrganizationsName'})),
    
    

]