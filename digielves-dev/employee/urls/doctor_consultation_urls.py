
from django.contrib import admin
from django.urls import path, include

from employee.views.doctor_consultation import ConsultationDetailsClass, DoctorConsultationClass, DoctorConsultationForFilterClass, DoctorsViewSet, DownloadReportClass, EmployeeConsultationCountClass, RescheduleConsultationClass, UpdateDoctorConsultationClass







urlpatterns = [


    path(r'book-doctor-consultation/',DoctorConsultationClass.as_view({'post':'BookAppointment'})),
    path(r'book-doctor-consultation-report/',DoctorConsultationClass.as_view({'post':'BookAppointmentForReport'})),
    path(r'get-doctor-appointment-details/',DoctorConsultationClass.as_view({'get':'GetBookingDetails'})),
    path(r'update-doctor-consultation/',UpdateDoctorConsultationClass.as_view({'put':'updateAppointment'})),
    
    
    path(r'get-appointment-list/',DoctorConsultationClass.as_view({'get':'GetConsultationList'})),

    path(r'reschedule-consultation/',RescheduleConsultationClass.as_view({'post':'rescheduleAppointment'})),
    
    
    path(r'add-consultation-details/',ConsultationDetailsClass.as_view({'post':'AddConsultationDetails'})),
    path(r'get-consultation-details/',ConsultationDetailsClass.as_view({'get':'GetConsultationDetails'})),



    path(r'get-available-doctors/',DoctorConsultationClass.as_view({'get':'getDoctor'})),


    path(r'get-doctors/',DoctorsViewSet.as_view({'get':'get_available_doctors'})),




    path(r'get-friend-nd-family/',DoctorConsultationForFilterClass.as_view({'get':'getFriendsndFamily'})),
    path(r'get-report-type/',DoctorConsultationForFilterClass.as_view({'get':'getReportType'})),
    path(r'check-cancel/',EmployeeConsultationCountClass.as_view({'get':'getCancellationCount'})),
    
    path(r'export-reports/',DownloadReportClass.as_view({'get':'downloadReportsPDF'})),
    
    path(r'consultation/add_report/',DoctorConsultationClass.as_view({'post':'AddReport'})),
] 
