
from django.contrib import admin
from django.urls import path, include

from employee.views.personal_details import EmployeeDetailsClass








urlpatterns = [


    path(r'add-details/',EmployeeDetailsClass.as_view({'post':'addEmployeeDetails'})),
    path(r'update-details/',EmployeeDetailsClass.as_view({'put':'updateEmployeeDetails'})),
    path(r'get-details/',EmployeeDetailsClass.as_view({'get':'getEmployeeDetails'})),

    path(r'update-profile-picture/',EmployeeDetailsClass.as_view({'put':'updateProfilePicture'})),
    path(r'get-profile-picture/',EmployeeDetailsClass.as_view({'get':'getProfilePicture'})),


    



    
]
