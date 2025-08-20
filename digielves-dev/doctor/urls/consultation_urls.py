
from django.contrib import admin
from django.urls import path, include

from doctor.view.consultation import  CancelConsultationClass, DoctorConsultationClass, RescheduleConsultationClass, UpdateDoctorConsultationClass








urlpatterns = [


    path(r'book-doctor-consultation/',DoctorConsultationClass.as_view({'post':'BookAppointment'})),
    path(r'get-doctor-appointment-details/',DoctorConsultationClass.as_view({'get':'GetBookingDetails'})),
    path(r'update-doctor-consultation/',UpdateDoctorConsultationClass.as_view({'put':'updateAppointment'})),
    path(r'update-consultation-status/',DoctorConsultationClass.as_view({'get':'updateConsultationStatus'})),
    path(r'delete-doctor-prescription/',DoctorConsultationClass.as_view({'delete':'DeleteDoctorPrescription'})),
    path(r'generate-consultation-summary/',DoctorConsultationClass.as_view({'get':'generateSummary'})),






    
    
    path(r'get-consultation/',DoctorConsultationClass.as_view({'get':'GetDoctorConsultation'})),

    path(r'get-completed-appointment-list/',DoctorConsultationClass.as_view({'get':'GetCompletedConsultationList'})),
    path(r'get-completed-and-upcoming-appointment-list/',DoctorConsultationClass.as_view({'get':'GetCompletedAndUpcomingConsultationList'})),




    path(r'get-appointment-list/',DoctorConsultationClass.as_view({'get':'GetConsultationList'})),

    
    

    path(r'reschedule-consultation/',RescheduleConsultationClass.as_view({'post':'rescheduleAppointment'})),
    path(r'cancel-consultation/',CancelConsultationClass.as_view({'post':'cancelAppointment'})),

    path(r'get-available-date/',CancelConsultationClass.as_view({'get':'GetDoctorAvailableDate'})),
    path(r'get-available-slots/',CancelConsultationClass.as_view({'get':'GetAvailableSlots'})),
    
    path(r'update-consultation/',UpdateDoctorConsultationClass.as_view({'put':'updateAndGeneratePrescription'})),
    
    path(r'test/generate_pdf/',UpdateDoctorConsultationClass.as_view({'post':'TestApiGetPdf'})),
    
 
]
