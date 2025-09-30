from django.urls import path
from employee.views.social_media.outlook_auth import OutlookAuthViewSet





urlpatterns = [

    path(r'social-media/outlook/create-auth/',OutlookAuthViewSet.as_view({'post':'AddOutlookAuth'})),
    path(r'social-media/outlook/get-auth/',OutlookAuthViewSet.as_view({'get':'get_auth_by_user_outlook'})),
    path(r'social-media/outlook/update-status-login/',OutlookAuthViewSet.as_view({'put':'update_status_login'})),
]