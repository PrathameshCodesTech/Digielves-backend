from django.contrib import admin
from django.urls import path, include

from digielves_setup.view.onboarding import TestMailClass, UserCreationClass




urlpatterns = [

    path(r'create-user/',UserCreationClass.as_view({'post':'createUser'})),
    path(r'create-bulk-user/',UserCreationClass.as_view({'post':'bulkCreateUser'})),
    path(r'get-organization-request-count/',UserCreationClass.as_view({'get':'organizationRequestCount'})),

    
    path(r'get-users/',UserCreationClass.as_view({'get':'getApprovedUser'})),
    path(r'update-rejected-employee/',UserCreationClass.as_view({'put':'update_rejected_employee'})),




    path(r'verify-user/',UserCreationClass.as_view({'post':'verifyUser'})),
    path(r'verify-doctor/',UserCreationClass.as_view({'post':'verifyDoctor'})),

    path(r'reject-user/',UserCreationClass.as_view({'post':'rejectUser'})),
    
    path(r'get-users-list/',UserCreationClass.as_view({'get':'getUserData'})),
    
    path(r'email-verification/',UserCreationClass.as_view({'post':'emailVerification'})),
    path(r'is-profile-verified/',UserCreationClass.as_view({'post':'isProfileVerified'})),
    


    path(r'get-data/',UserCreationClass.as_view({'get':'getData'})),
    path(r'admin-level/update-status/',UserCreationClass.as_view({'put':'update_active_status'})),
    path(r'organization/update-status/',UserCreationClass.as_view({'put':'update_active_status_emp'})),
    
    path(r'delete-created-user/',UserCreationClass.as_view({'delete':'deleteRequest'})),
    path(r'inactive-bulk-user/',UserCreationClass.as_view({'put':'bulkCancelUser'})),
    path(r'resend_mail/',UserCreationClass.as_view({'post':'resend_mail'})),
    
    path(r'hierarchy/add_hierarchy/',UserCreationClass.as_view({'post':'add_hierarchy'})),
    path(r'get_email/',UserCreationClass.as_view({'get':'get_email'})),
    
    path(r'hierarchy/get_hierarchy/',UserCreationClass.as_view({'get':'get_hierarchy'})),
    path(r'hierarchy/update_hierarchy/',UserCreationClass.as_view({'put':'update_hierarchy'})),
    path(r'hierarchy/delete_hierarchy/',UserCreationClass.as_view({'delete':'delete_hierarchy'})),
    
    path(r'test/send_mail/',TestMailClass.as_view({'get':'test_mail'})),
    
    
    
]