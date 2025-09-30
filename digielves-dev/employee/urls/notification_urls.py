from django.contrib import admin
from django.urls import path, include

from employee.views.notification import NotificationClass



urlpatterns = [

    path(r'notify/',NotificationClass.as_view({'get':'get_notifications'})),
    path(r'update-notify/',NotificationClass.as_view({'put':'update_notifications'})),
    path(r'notification/mark_clicked/',NotificationClass.as_view({'put':'mark_notifications_as_clicked'})),
    
]