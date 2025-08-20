
from django.contrib import admin
from django.urls import path, include

from digielves_setup.view.profile import ProfileViewSet








urlpatterns = [


    path(r'get-profile/',ProfileViewSet.as_view({'get':'get_profile'})),
    path(r'update-profile/',ProfileViewSet.as_view({'put':'update_user_profile'})),

]