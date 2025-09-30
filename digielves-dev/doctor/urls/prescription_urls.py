from django.contrib import admin
from django.urls import path, include
from doctor.view.prescription import DoctorPrescriptionClass, MedicineClass



urlpatterns = [

    path(r'add-prescription/',DoctorPrescriptionClass.as_view({'post':'addDoctorPrescription'})),
    path(r'get-prescription/',DoctorPrescriptionClass.as_view({'get':'getDoctorPrescription'})),
    
    path(r'add-medicines/',MedicineClass.as_view({'post':'AddMedicine'})),
    path(r'get-medicines/',MedicineClass.as_view({'get':'getMedicine'})),

    



]