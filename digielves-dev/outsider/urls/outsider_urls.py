from django.urls import path

from outsider.views.outsider import OutsiderCustomBoardViewSets, OutsiderInEmployeeViewSets, OutsiderViewSets





urlpatterns = [

    path(r'employee/get_outsiders/',OutsiderInEmployeeViewSets.as_view({'get':'get_outsiders'})),
    path(r'employee/give_access/',OutsiderInEmployeeViewSets.as_view({'post':'give_access'})),
    path(r'employee/access/get_task/',OutsiderInEmployeeViewSets.as_view({'get':'get_accessed_task'})),
    
    path(r'outsider/get_task/',OutsiderViewSets.as_view({'get':'get_accessed_task_new'})),
    
    path(r'outsider/get_boards/',OutsiderCustomBoardViewSets.as_view({'get':'get_outsider_boards'})),
    path(r'outsider/get_board_task/',OutsiderCustomBoardViewSets.as_view({'get':'get_customboard_data'})),
    path(r'outsider/get_status/',OutsiderCustomBoardViewSets.as_view({'get':'get_task_status'})),
    
    
]