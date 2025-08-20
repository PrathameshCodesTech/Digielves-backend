
from django.urls import path

from employee.views.sales_lead import SalesExportAndImportViewSet, SalesFollowupViewSet, SalesLeadViewSet, SalesSpecialAccessViewSet, SalesStatusViewSet


urlpatterns = [

    path(r'create-lead/',SalesLeadViewSet.as_view({'post':'create_lead'})),
    path(r'get-lead/',SalesLeadViewSet.as_view({'get':'getSalesLead'})),
    path(r'update-lead/',SalesLeadViewSet.as_view({'put':'update_lead'})),
    path(r'get-lead_details/',SalesLeadViewSet.as_view({'get':'getSpecificSalesLeadDetails'})),
    path(r'update_lead_details/',SalesLeadViewSet.as_view({'put':'changeIndividualLeadStatus'})),
    path(r'status/get_sales_status/',SalesStatusViewSet.as_view({'get':'get_sales_status'})),
    path(r'delete/',SalesLeadViewSet.as_view({'delete':'delete_lead'})),
    
    # path(r'sales/import/',SalesExportAndImportViewSet.as_view({'get':'ImportExcel'})),
    path(r'add-follow_up/',SalesFollowupViewSet.as_view({'post':'create_sales_followup'})),
    path(r'get-follow_up/',SalesFollowupViewSet.as_view({'get':'get_sales_lead_followup'})),
    path(r'add-note/',SalesFollowupViewSet.as_view({'post':'create_note'})),
    
    path(r'give_access/',SalesSpecialAccessViewSet.as_view({'post':'give_access'})),
    
    path(r'access/get_leads/',SalesSpecialAccessViewSet.as_view({'get':'get_leads_of_accessed_user'})),
    
    
    path(r'import/',SalesExportAndImportViewSet.as_view({'post':'ImportExcel'})),
     
     path(r'update-next_followup_date/',SalesLeadViewSet.as_view({'put':'changeNextFollowupDate'})),
    path(r'delete_slse_dael/',SalesLeadViewSet.as_view({'delete':'delete_sales_leads_by_user'})),
]


