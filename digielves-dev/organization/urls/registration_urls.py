from django.contrib import admin
from django.urls import path, include

from organization.views.registration import Registration


urlpatterns = [

    path(r'registration/',Registration.as_view({'post':'UserRegistraion'})),
    # path(r'sso-registration/',Registration.as_view({'post':'SSOUserRegistraion'})),
    path(r'update-registration/',Registration.as_view({'post':'UpdateUserRegistraion'})),




]