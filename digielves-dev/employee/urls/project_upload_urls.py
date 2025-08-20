from django.contrib import admin
from django.urls import path, include

from employee.views.project_upload import UploadProjectViewSet



urlpatterns = [

    path(r'project/upload/',UploadProjectViewSet.as_view({'post':'upload_project'})),
    path(r'project/mapping/',UploadProjectViewSet.as_view({'post':'map_data'})),
    
    # path(r'update-registration/',UploadProjectViewSet.as_view({'post':'UpdateUserRegistraion'})),




]