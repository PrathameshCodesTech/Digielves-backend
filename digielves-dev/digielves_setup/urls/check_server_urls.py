
from django.contrib import admin
from django.urls import path, include

from digielves_setup.view.server_check_api import CheckClass








urlpatterns = [


    path(r'check_res/',CheckClass.as_view({'get':'check_server'})),    

]