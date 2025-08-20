from django.contrib import admin
from django.urls import path, include
from doctor.view.personal_details import DoctorDetailsClass



urlpatterns = [

    path(r'add-details/',DoctorDetailsClass.as_view({'post':'addDetails'})),
    path(r'update-details/',DoctorDetailsClass.as_view({'put':'updateDetails'})),
    path(r'get-details/',DoctorDetailsClass.as_view({'get':'getDetails'})),

    
    
    
    path(r'add-doctor-attachment/',DoctorDetailsClass.as_view({'post':'addDoctorAchivement'})),


    path(r'update-profile-picture/',DoctorDetailsClass.as_view({'put':'updateProfilePicture'})),
    path(r'get-profile-picture/',DoctorDetailsClass.as_view({'get':'getProfilePicture'})),


]