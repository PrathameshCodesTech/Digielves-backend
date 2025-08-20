from django.urls import path

from employee.views.social_media.meta_auth import MetaAuthViewSet






urlpatterns = [

    path(r'social-media/meta/add-auth/',MetaAuthViewSet.as_view({'post':'AddmetaAuth'})),
    path(r'social-media/meta/get-auth/',MetaAuthViewSet.as_view({'get':'get_auth_by_user_meta'})),
    path(r'social-media/meta/update-auth/',MetaAuthViewSet.as_view({'put':'update_meta_auth'})),
    path(r'social-media/meta/update-status-login/',MetaAuthViewSet.as_view({'put':'update_status_login'})),
    path(r'social-media/meta/get-check-auth/',MetaAuthViewSet.as_view({'get':'get_user_meta_auth'})), #it is for check before entry in facebook page

]