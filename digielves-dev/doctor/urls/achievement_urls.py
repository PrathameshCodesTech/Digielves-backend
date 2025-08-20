from django.contrib import admin
from django.urls import path, include
from doctor.view.doctor_achivement import DoctorAchievemnetsClass



urlpatterns = [

    path(r'add-achievements/',DoctorAchievemnetsClass.as_view({'post':'addDoctorAchivement'})),
    path(r'get-achievements/',DoctorAchievemnetsClass.as_view({'get':'getAchievements'})),
    path(r'delete-achievements/',DoctorAchievemnetsClass.as_view({'delete':'deleteAchievements'})),

    



]