from django.contrib import admin
from django.urls import path, include

from employee.views.cards.business_card import BusinessCardViewSet




urlpatterns = [

    path(r'card/add-business_card/',BusinessCardViewSet.as_view({'post':'add_business_card'})),
    path(r'card/get-business_card/',BusinessCardViewSet.as_view({'get':'get_business_cards'})),
    path(r'card/delete-business_card/',BusinessCardViewSet.as_view({'delete':'delete_business_card'})),
    path(r'card/update-business_card/',BusinessCardViewSet.as_view({'put':'update_business_card'})),

    path(r'card/send-business_card/',BusinessCardViewSet.as_view({'post':'send_business_card'})),
]