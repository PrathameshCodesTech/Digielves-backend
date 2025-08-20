
from django.urls import path

from admin_app.views.consultation import DoctorConsultationAdminClass





urlpatterns = [

    path(r'consultation/get-consultations/',DoctorConsultationAdminClass.as_view({'get':'GetDoctorConsultationForAdmin'}))

] 