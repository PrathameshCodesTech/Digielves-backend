from django.urls import path

from employee.views.social_media.socialmedia import SocialMediaAuthViewSet, SocialMediaViewSet




urlpatterns = [

    path(r'social-media/active/',SocialMediaViewSet.as_view({'post':'AddSocialmedia'})),
    path(r'social-media/get-active-social-media/',SocialMediaViewSet.as_view({'get':'get_social_media_by_user'})),
    path(r'social-media/update-active-social-media/',SocialMediaViewSet.as_view({'put':'UpdateSocialMedia'})),
    path(r'social-media/get-auth-info/',SocialMediaAuthViewSet.as_view({'get':'get_auth_info'})),

]