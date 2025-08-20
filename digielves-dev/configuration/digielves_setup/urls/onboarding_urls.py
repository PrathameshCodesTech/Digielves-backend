from django.contrib import admin
from django.urls import path, include

from digielves_setup.view.onboarding import UserCreationClass




urlpatterns = [

    path(r'create-user/',UserCreationClass.as_view({'post':'createUser'})),
    path(r'verify-user/',UserCreationClass.as_view({'post':'verifyUser'})),
    path(r'verify-doctor/',UserCreationClass.as_view({'post':'verifyDoctor'})),

    path(r'reject-user/',UserCreationClass.as_view({'post':'rejectUser'})),
    
    path(r'get-users-list/',UserCreationClass.as_view({'get':'getUserData'})),
    
    path(r'email-verification/',UserCreationClass.as_view({'post':'emailVerification'})),
    path(r'is-profile-verified/',UserCreationClass.as_view({'post':'isProfileVerified'})),


    path(r'get-data/',UserCreationClass.as_view({'get':'getData'})),


    path(r'outlook-login/',OutlookLogInClass.as_view({'post':'logIn'}))


]