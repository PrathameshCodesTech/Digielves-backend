from django.contrib import admin
from django.urls import path, include

from digielves_setup.view.yahoo_login import YahooLogInClass




urlpatterns = [

    # path(r'yahoo-login/',YahooLogInClass.as_view({'get':'yahoo_login'})),

    path('yahoo-login/', YahooLogInClass.as_view({'get': 'send_to_login'})),
    path('yahoo-token/', YahooLogInClass.as_view({'get': 'get_tokens'})),
    path('yahoo-info/', YahooLogInClass.as_view({'get': 'get_user_info'})), 


 


]