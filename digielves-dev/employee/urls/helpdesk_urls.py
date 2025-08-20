from django.contrib import admin
from django.urls import path, include

from employee.views.helpdesk import HelpdeskViewSet,HelpdeskActionViewSet



urlpatterns = [

    path(r'helpdesk/raise-issue/',HelpdeskViewSet.as_view({'post':'raise_issue'})),
    path(r'helpdesk/get-raise-issue/',HelpdeskViewSet.as_view({'get':'get_raised_issue'})),
    path(r'helpdesk/create-issue-action/',HelpdeskActionViewSet.as_view({'post':'raise_issue_action'})),
    path(r'helpdesk/get-assigned-issue/',HelpdeskViewSet.as_view({'get':'get_assigned_issue'})),
    path(r'helpdesk/get_issues_nd_action/',HelpdeskViewSet.as_view({'get':'get_issues_nd_action'})),

]