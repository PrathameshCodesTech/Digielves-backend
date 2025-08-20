from django.urls import path
from employee.views.social_media.gmail_auth import GmailAuthViewSet, GmailEmailViewSet





urlpatterns = [

    path(r'social-media/gmail/create-auth/',GmailAuthViewSet.as_view({'post':'AddGmailAuth'})),
    path(r'social-media/gmail/get-auth/',GmailAuthViewSet.as_view({'get':'get_auth_by_user_gmail'})),
    path(r'social-media/gmail/update-status-login/',GmailAuthViewSet.as_view({'put':'update_status_login'})),
    
    path(r'social-media/gmail/add-email/',GmailEmailViewSet.as_view({'post':'add_email'})),
    path(r'social-media/gmail/get-email/',GmailEmailViewSet.as_view({'get':'get_email'})),
]