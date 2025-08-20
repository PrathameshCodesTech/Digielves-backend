
from django.contrib import admin
from django.urls import path, include

from digielves_setup.view.address import UserAddressClass







urlpatterns = [


    path(r'add-address/',UserAddressClass.as_view({'post':'addUserAddress'})),
    path(r'update-address/',UserAddressClass.as_view({'put':'updateUserAddress'}))
    
    # path(r'get-address/',PartnerAddressClass.as_view({'get':'getPartnerPersonalDetails'})),
    

]