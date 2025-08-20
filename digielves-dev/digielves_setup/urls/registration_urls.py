from django.contrib import admin
from django.urls import path, include

from digielves_setup.view.registration import Registration


urlpatterns = [
    
    path(r'create-admin/',Registration.as_view({'post':'AdminRegistration'})),
    # path(r'decode-it/',Registration.as_view({'post':'DecodePassword'})),
    

    path(r'registration/',Registration.as_view({'post':'UserRegistraion'})),
    
    path(r'delete-user/',Registration.as_view({'delete':'delete_user'})),
    # path(r'sso-registration/',Registration.as_view({'post':'SSOUserRegistraion'})),
    path(r'update-registration/',Registration.as_view({'post':'UpdateUserRegistraion'})),
    path(r'get-registration/',Registration.as_view({'get':'getUserData'})),




]