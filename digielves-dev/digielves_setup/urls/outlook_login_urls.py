from django.contrib import admin
from django.urls import path, include

from digielves_setup.view.outlook_login import OutlooklogIn

from digielves_setup.view.outlook_login import OutlookLogInClass



urlpatterns = [

  
    path('outlook-login/', OutlooklogIn, name='html_response'),

    path(r'get-outlook-token/',OutlookLogInClass.as_view({'get':'get_outlookTokens'})),


]