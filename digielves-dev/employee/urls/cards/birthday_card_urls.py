
from django.contrib import admin
from django.urls import path, include

from employee.views.cards.birthday_card import BirthdayViewSet









urlpatterns = [


    path(r'bd/get_user_details/',BirthdayViewSet.as_view({'get':'get_user_details'})),
    path(r'bd/add_card/',BirthdayViewSet.as_view({'put':'add_bd_card'})),
    path(r'bd/get_bd_templates/',BirthdayViewSet.as_view({'get':'get_bd_templates'})),


    



    
]
