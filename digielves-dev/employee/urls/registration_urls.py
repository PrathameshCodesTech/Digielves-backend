from django.contrib import admin
from django.urls import path, include

from employee.views.registration import Registration,UpdateRegistration


urlpatterns = [

    path(r'registration/',Registration.as_view({'post':'UserRegistraion'})),
    # path(r'sso-registration/',Registration.as_view({'post':'SSOUserRegistraion'})),
    path(r'update-registration/',UpdateRegistration.as_view({'post':'UpdateUserRegistraion'})),




]