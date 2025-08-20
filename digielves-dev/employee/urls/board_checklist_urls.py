
from django.urls import path
from employee.views.board import *
from employee.views.board_checklist import BoardCheckListViewSet




urlpatterns = [

    path(r'board/add-board-checklist/',BoardCheckListViewSet.as_view({'post':'AddBoardCheckList'})),
    path(r'board/get-board-checklist/',BoardCheckListViewSet.as_view({'get':'getBoardCheckList'})),
    path(r'board/update-board-checklist/',BoardCheckListViewSet.as_view({'put':'updateBoard'})),
    path(r'board/delete-board-checklist/',BoardCheckListViewSet.as_view({'delete':'deleteBoardCheckList'})),
    path(r'board/checklist/update-checklist-sequence/',BoardCheckListViewSet.as_view({'put':'updateChecklistSequence'}))
]