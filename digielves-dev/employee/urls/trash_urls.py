from django.contrib import admin
from django.urls import path, include

from employee.views.trash import TasksTrashViewSet




urlpatterns = [

    path(r'trash/get-trash/',TasksTrashViewSet.as_view({'get':'getTrashed_task'})),
    path(r'trash/restore/',TasksTrashViewSet.as_view({'put':'Update_to_unTrash'})),  # make it restore
    path(r'trash/delete-task/',TasksTrashViewSet.as_view({'delete':'PermanantdeleteTask'})),
]