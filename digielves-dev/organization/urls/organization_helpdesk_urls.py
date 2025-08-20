


from django.urls import path

from organization.views.organization_helpdesk import HelpDeskActionViewSet, HelpDeskViewSet



urlpatterns = [

    path(r'helpdesk/update-raise-issue/',HelpDeskViewSet.as_view({'put':'updateHelpdesk'})),
    path(r'helpdesk/get-raise-issue/',HelpDeskViewSet.as_view({'get':'get_raised_issue'})),
    path(r'helpdesk/get-issue-action/',HelpDeskActionViewSet.as_view({'get':'get_helpdesk_actions'})),
    path(r'helpdesk/get-issue-nd-action/',HelpDeskViewSet.as_view({'get':'get_issues_nd_action'})),
    path(r'helpdesk/get-user/',HelpDeskViewSet.as_view({'get':'get_users'})),


]