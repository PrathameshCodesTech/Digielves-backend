from django.contrib import admin
from django.urls import path, include

from doctor.view.doctor_slot import DoctorSlotViewSet






urlpatterns = [

    # path(r'add-slot/',DoctorSlotViewSet.as_view({'post':'AddSlots'})),
    
    path(r'add-slot/',DoctorSlotViewSet.as_view({'post':'AddSlot'})),


    path(r'get-slots/',DoctorSlotViewSet.as_view({'get':'GetSlots'})),

    path(r'get-today-my-slots/',DoctorSlotViewSet.as_view({'get':'get_today_slots'})),

    path(r'update-slots-freeze/',DoctorSlotViewSet.as_view({'put':'UpdateSlotFreeze'})),
    
    path(r'update-leave/',DoctorSlotViewSet.as_view({'put':'UpdateLeave'})),

    path(r'update-slots-nd-consultation/',DoctorSlotViewSet.as_view({'put':'update_slots_and_consultations'})),

    path(r'delete-doctor-slots/',DoctorSlotViewSet.as_view({'delete':'delete_slots'})),

]