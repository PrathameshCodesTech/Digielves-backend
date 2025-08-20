from django.contrib import admin
from django.urls import path, include

from digielves_setup.view.outlook_login import OutlookLogInClass



urlpatterns = [

    path(r'outlook-login/',OutlookLogInClass.as_view({'post':'logIn'}))


]