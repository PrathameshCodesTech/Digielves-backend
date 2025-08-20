from django.contrib import admin
from django.urls import path, include

from employee.views.template import *
from employee.views.users import UserViewSet


urlpatterns = [

    path(r'get-users/',UserViewSet.as_view({'get':'get_users'})),
    path(r'get-user_details/',UserViewSet.as_view({'get':'get_users_details'})),
]