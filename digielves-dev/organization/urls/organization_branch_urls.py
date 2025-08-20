from django.contrib import admin
from django.urls import path, include
from organization.views.organization_branch import OrgBranchViewSet





urlpatterns = [

    path(r'add-branch/',OrgBranchViewSet.as_view({'post':'AddBranch'})),

    path(r'get-organizations/',OrgBranchViewSet.as_view({'get':'get_organizations_nd_branch'})),
    
    path(r'get-organization-branch/',OrgBranchViewSet.as_view({'get':'get_organization_branch_by_user_and_org'})),
    
    path(r'get-branch-employee/',OrgBranchViewSet.as_view({'get':'get_Employee_by_branch'})),

]