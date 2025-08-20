from django.contrib import admin
from django.urls import path, include

from organization.views.hierarchy.hierarchy import TreeHierarchyViewSet





urlpatterns = [

    path(r'reporting_relationships/get_tree/',TreeHierarchyViewSet.as_view({'get':'get_reporting_tree'})),

    path(r'reporting_relationships/get_employee/',TreeHierarchyViewSet.as_view({'get':'get_employee'})),
    
    path(r'reporting_relationships/add_user_positions/',TreeHierarchyViewSet.as_view({'post':'add_user_positions'})),
]