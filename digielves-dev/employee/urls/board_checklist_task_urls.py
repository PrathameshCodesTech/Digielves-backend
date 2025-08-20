from django.urls import path
from employee.views.board import *
from employee.views.board_checklist import BoardCheckListViewSet
from employee.views.board_checklist_task import BoardCheckListTaskViewSet




urlpatterns = [

    path(r'board/add-task/',BoardCheckListTaskViewSet.as_view({'post':'create_task'})),
    path(r'board/get-checklist-task/',BoardCheckListViewSet.as_view({'get':'getBoardCheckList'})),
    path(r'board/update-checklist-task/',BoardCheckListViewSet.as_view({'put':'updateBoard'})),
    path(r'board/delete-checklist-task/',BoardCheckListViewSet.as_view({'delete':'deleteBoardCheckList'})),

    path(r'board/get-user-task/',BoardCheckListTaskViewSet.as_view({'get':'getRemainingUsers'}))
]