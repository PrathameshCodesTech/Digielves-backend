from django.contrib import admin
from django.urls import path
from organization.views.sales_status import SalesStatusViewSet



urlpatterns = [
    path(r'create_status/',SalesStatusViewSet.as_view({'post':'AddStatus'})),
    path(r'update_status_field/',SalesStatusViewSet.as_view({'put':'updateSalesStatusField'})),
    path(r'get_status_fields/',SalesStatusViewSet.as_view({'get':'getStatuses'})),
    path(r'delete_status/',SalesStatusViewSet.as_view({'delete':'deleteStatus'})),
    

]