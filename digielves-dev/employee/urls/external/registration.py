
from django.urls import path

from employee.views.external.registration import UserRegDetailsView, UserWithOrganizationDetailsView



urlpatterns = [

    path(r'external/create-organization/',UserWithOrganizationDetailsView.as_view({'post':'create_organization'})),
    path(r'external/create-user/',UserRegDetailsView.as_view({'post':'register_employee'})),
    path(r'external/login/',UserRegDetailsView.as_view({'post':'ExternalUserlogIn'})),
]