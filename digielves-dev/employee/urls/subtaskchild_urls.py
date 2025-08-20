from django.contrib import admin
from django.urls import path, include

from employee.views.subtaskchild import SubTaskChildViewSet




urlpatterns = [

    path(r'subtask/child/create/',SubTaskChildViewSet.as_view({'post':'create_subtask_child'})),
    path(r'subtask/child/update/',SubTaskChildViewSet.as_view({'put':'UpdateSubTaskChild'})),
    
    path(r'subtask/child/get/',SubTaskChildViewSet.as_view({'get':'get_subtask_child'})),
    path(r'subtask/child/delete/',SubTaskChildViewSet.as_view({'delete':'delete_subTask_child'})),
    
]