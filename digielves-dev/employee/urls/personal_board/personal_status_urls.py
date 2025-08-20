from django.contrib import admin
from django.urls import path, include

from employee.views.personal_board.personal_status import PersonalStatusViewSet


urlpatterns = [
    path(r'create_status/',PersonalStatusViewSet.as_view({'post':'AddPersonalStatus'})),
    path(r'update_status_field/',PersonalStatusViewSet.as_view({'put':'updatePersonalTasksStatusField'})),
    path(r'get_status_fields/',PersonalStatusViewSet.as_view({'get':'getStatuses'})),
    path(r'delete_status/',PersonalStatusViewSet.as_view({'delete':'deleteStatus'})),
  
]