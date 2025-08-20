from django.urls import path

from employee.views.social_media.socialmedia import SocialMediaAuthViewSet, SocialMediaViewSet
from employee.views.social_media.telegram_auth import TelegramAuthViewSet, TelegramMessageViewSet, TelegramUserViewSet




urlpatterns = [

    path(r'social-media/telegram/add-mobile/',TelegramAuthViewSet.as_view({'post':'create_telegram_auth'})),
    path(r'social-media/telegram/add-otp/',TelegramAuthViewSet.as_view({'post':'add_otp'})),
    
    path(r'social-media/telegram/get-auth/',TelegramAuthViewSet.as_view({'get':'get_user_telegram_auth'})),


    path(r'social-media/telegram/add-user/',TelegramUserViewSet.as_view({'post':'Add_user'})),
    path(r'social-media/telegram/delete-user/',TelegramUserViewSet.as_view({'delete':'delete_username'})),
    path(r'social-media/telegram/get-user-users/',TelegramUserViewSet.as_view({'get':'get_user'})),


    path(r'social-media/telegram/send-message/',TelegramMessageViewSet.as_view({'post':'send_telegram_message'})),
    path(r'social-media/telegram/get-messages/',TelegramMessageViewSet.as_view({'get':'get_telegram_message'})),

    path(r'social-media/telegram/update-status/',TelegramAuthViewSet.as_view({'put':'update_status_login'})),
]


