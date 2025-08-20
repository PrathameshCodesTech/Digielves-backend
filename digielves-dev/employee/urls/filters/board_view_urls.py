from django.contrib import admin
from django.urls import path, include

from employee.views.filters.board_view import BoardViewFilterViewSet






urlpatterns = [

    path(r'filter/add-filter/',BoardViewFilterViewSet.as_view({'post':'add_board_view_filter'})),
  

]