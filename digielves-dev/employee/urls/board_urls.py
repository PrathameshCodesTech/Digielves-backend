from django.contrib import admin
from django.urls import path, include
from employee.views.board import BoardAccessViewSet, BoardViewSet

from employee.views.template import *


urlpatterns = [

    path(r'add-board/',BoardViewSet.as_view({'post':'AddBoard'})),
    path(r'get-board/',BoardViewSet.as_view({'get':'getBoard'})),
    path(r'get-user-board/',BoardViewSet.as_view({'get':'getBoards'})),
    path(r'custom_board/get-tasks/',BoardViewSet.as_view({'get':'GetCustomBoardData'})),
    path(r'get-board-users/',BoardViewSet.as_view({'get':'get_users'})),

    path(r'board/get-users-in-board/',BoardViewSet.as_view({'get':'get_users_in_board'})),

    path(r'update-board-template/',BoardViewSet.as_view({'put':'UpdateBoard'})),
    
    path(r'board/update-board-assign/',BoardViewSet.as_view({'put':'UpdateBoardAssignTo'})),
    path(r'update-board/',BoardViewSet.as_view({'put':'updateBoard'})),
    path(r'delete-board/',BoardViewSet.as_view({'delete':'deleteBoard'})),
    
    path(r'board/get_board_sections/',BoardViewSet.as_view({'get':'get_sections'})),
    path(r'board/get_existing_board_users/',BoardViewSet.as_view({'get':'get_users_in_board'})),
    
    path(r'board/update_date/',BoardViewSet.as_view({'put':'update_board_due_date'})),
    
    path(r'board/give_permission/',BoardAccessViewSet.as_view({'post':'add_permission'})),
    path(r'board/get_permission/',BoardAccessViewSet.as_view({'get':'get_permission'})), 
    path(r'board/get-access_given_users/',BoardAccessViewSet.as_view({'get':'get_permission_given_users'})), 
    
    path(r'board/give_task_permission/',BoardAccessViewSet.as_view({'post':'give_task_permissions_in_board'})),
    path(r'board/get_task_permission/',BoardAccessViewSet.as_view({'get':'get_task_permission_given_users'})),
    
    path(r'board/add_to-favorite/',BoardViewSet.as_view({'put':'make_favorite'}))
]