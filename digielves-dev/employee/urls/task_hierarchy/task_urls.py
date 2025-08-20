from django.urls import path

from employee.views.task_hierarchy.task import SaveTemplateView, TaskHierarchyChatViewSet, TaskHierarchyChildrenViewSet, TaskHierarchyCommentViewSet, TaskHierarchyCustomBoardViewSet, TaskHierarchyCustomizeViewSet, TaskHierarchyDependenciesViewSet, TaskHierarchyMyDayViewSet, TaskHierarchyRequestViewSet, TaskHierarchyTrashViewSet, TaskHierarchyViewSet





urlpatterns = [

    path(r'create_task/',TaskHierarchyViewSet.as_view({'post':'create_task'})),
    path(r'my_board/get-task/',TaskHierarchyViewSet.as_view({'get':'get_myboard_task'})),
    path(r'task/update-status/',TaskHierarchyViewSet.as_view({'put':'change_task_status'})),
    path(r'task/get_task_assigned_users/',TaskHierarchyViewSet.as_view({'get':'get_task_assigned_users'})),
    path(r'task/relocate-task/',TaskHierarchyViewSet.as_view({'put':'update_task_to_other_checklist'})),
    
    path(r'delete_task/',TaskHierarchyViewSet.as_view({'delete':'delete_task'})),
    
    path(r'task/update_task/',TaskHierarchyViewSet.as_view({'put':'update_user_tasks'})),
    
    
    path(r'task/children/get_task/',TaskHierarchyChildrenViewSet.as_view({'get':'get_task_in_tasks'})),
    path(r'task/children/get_task_bulk/',TaskHierarchyChildrenViewSet.as_view({'get':'get_task_children'})),
    path(r'task/children/get_task_bulk_test/',TaskHierarchyChildrenViewSet.as_view({'get':'get_user_tasks_test'})),
    
    
    # depend on api's
    path(r'task/get-depend_on/',TaskHierarchyDependenciesViewSet.as_view({'get':'get_dependent_tasks'})),
    path(r'task/get-dependencies/',TaskHierarchyDependenciesViewSet.as_view({'get':'get_tasks_for_dependencies'})),
    
    path(r'task/update-dependencies/',TaskHierarchyDependenciesViewSet.as_view({'put':'update_dependencies'})),
    
    path(r'task/my_day/get-task/',TaskHierarchyMyDayViewSet.as_view({'get':'get_myday_user_task'})),
    
    path(r'task/custom_board/get-task/',TaskHierarchyCustomBoardViewSet.as_view({'get':'get_custom_board_data'})),
    
    path(r'custom_board/get-boards/',TaskHierarchyCustomBoardViewSet.as_view({'get':'get_boards'})),
    path(r'custom_board/template/add-task/',TaskHierarchyCustomBoardViewSet.as_view({'put':'add_selected_template_to_board'})),
    
    
    # trash api's
    path(r'tasks/trash/',TaskHierarchyTrashViewSet.as_view({'delete':'delete_task_data'})),
    path(r'tasks/trashed/',TaskHierarchyTrashViewSet.as_view({'get':'get_trashed_task'})),
    path(r'tasks/untrash/',TaskHierarchyTrashViewSet.as_view({'put':'untrash_task_data'})),
    path(r'tasks/trashed/delete/',TaskHierarchyTrashViewSet.as_view({'delete':'parmanant_delete_task'})),
    
    
    # Due Date Request
    path(r'task/request/create/',TaskHierarchyRequestViewSet.as_view({'post':'make_request'})),
    path(r'task/request/get/',TaskHierarchyRequestViewSet.as_view({'get':'get_requests'})),
    path(r'task/request/update/',TaskHierarchyRequestViewSet.as_view({'put':'update_request'})),
    path(r'task/request/delete/',TaskHierarchyRequestViewSet.as_view({'delete':'delete_request'})),
    
    # Task Comments
    path(r'task/add-comment/',TaskHierarchyCommentViewSet.as_view({'post':'createTaskComment'})),
    path(r'task/get-comments/',TaskHierarchyCommentViewSet.as_view({'get':'get_task_comments'})),
    
    # Task Chat
    path(r'task/add-message/',TaskHierarchyChatViewSet.as_view({'post':'createTaskChatting'})),
    path(r'task/get-chats/',TaskHierarchyChatViewSet.as_view({'get':'get_task_chats_and_activities'})),
    
    # custom combine Task and meeting
    path(r'get-meeting_and_tasks/',TaskHierarchyCustomizeViewSet.as_view({'get':'get_meetings_and_tasks'})),
    
    # save template
    path(r'template/save_template/',SaveTemplateView.as_view({'put':'save_template'})),
]