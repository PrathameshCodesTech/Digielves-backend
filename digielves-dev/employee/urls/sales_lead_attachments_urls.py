
from django.urls import path
from employee.views.sales_lead_attachments import SalesAttachmentViewSet


urlpatterns = [

    path(r'sales/add_attachment/',SalesAttachmentViewSet.as_view({'post':'createSalesAttachment'})),
    path(r'sales/get_attachment/',SalesAttachmentViewSet.as_view({'get':'getSalesAttachment'})),
    path(r'sales/delete_attachment/',SalesAttachmentViewSet.as_view({'delete':'deleteSalesAttachment'}))
]