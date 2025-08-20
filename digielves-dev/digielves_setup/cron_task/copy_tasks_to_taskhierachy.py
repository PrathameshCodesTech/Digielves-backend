from django.db import transaction

from digielves_setup.models import SubTaskChild, SubTasks, TaskAction, TaskAttachments, TaskChatting, TaskChecklist, TaskHierarchy, TaskHierarchyAction, TaskHierarchyAttachments, TaskHierarchyChatting, TaskHierarchyChecklist, Tasks

def copy_tasks_to_task_hierarchy():
    user_ids = [4,32, 50, 51, 53,66, 105,106,  107, 131] 
    # user_ids = []
    try:
        with transaction.atomic():
            tasks = Tasks.objects.filter(created_by_id__in=user_ids, inTrash = False)
            
            for task in tasks:
                print(task)
                # Retrieve and set the start_date for the task based on TaskHierarchyAction
                start_date = None
                first_status_change_action = TaskAction.objects.filter(
                    task__id=task.id,
                    remark__icontains="Task status has been updated"
                ).order_by('created_at').first()
                
                if first_status_change_action:
                    start_date = first_status_change_action.created_at
                
                task_hierarchy_instance = TaskHierarchy.objects.create(
                    created_by=task.created_by,
                    checklist=task.checklist,
                    task_topic=task.task_topic,
                    due_date=task.due_date,
                    task_description=task.task_description,
                    urgent_status=task.urgent_status,
                    status=task.status,
                    sequence=task.sequence,
                    is_personal=task.is_personal,
                    reopened_count=task.reopened_count,
                    inTrash=task.inTrash,
                    project_file_name=task.project_file_name,
                    start_date=start_date if start_date else task.start_date,
                    end_date=task.end_date,
                )
                task_hierarchy_instance.assign_to.set(task.assign_to.all())
                
                task_actions = TaskAction.objects.filter(task=task)
                for action in task_actions:
                    TaskHierarchyAction.objects.create(
                        user_id=action.user_id,
                        task=task_hierarchy_instance,
                        remark=action.remark,
                        created_at=action.created_at,
                        updated_at=action.updated_at,
                    )

                # Copy TaskChatting to TaskHierarchyChatting
                task_chats = TaskChatting.objects.filter(task=task)
                for chat in task_chats:
                    TaskHierarchyChatting.objects.create(
                        task=task_hierarchy_instance,
                        sender=chat.sender,
                        message=chat.message,
                        is_read=chat.is_read,
                        created_at=chat.created_at
                        )
                    
                    
                task_attachments = TaskAttachments.objects.filter(task=task)
                for attachment in task_attachments:
                    TaskHierarchyAttachments.objects.create(
                        created_by=task.created_by,
                        task=task_hierarchy_instance,
                        task_attachment=attachment.attachment,
                        created_at=attachment.created_at,
                        updated_at=attachment.updated_at,
                    )
                    
                task_checklists = TaskChecklist.objects.filter(Task=task)
                for checklist in task_checklists:
                    TaskHierarchyChecklist.objects.create(
                        Task=task_hierarchy_instance,
                        created_by=checklist.created_by,
                        name=checklist.name,
                        inTrash=checklist.inTrash,
                        trashed_with=checklist.trashed_with,
                        reopened_count=checklist.reopened_count,
                        completed=checklist.completed,
                        created_at=checklist.created_at,
                        updated_at=checklist.updated_at,
                    )
                # Handle SubTasks
                subtasks = SubTasks.objects.filter(Task=task, inTrash = False)
                for subtask in subtasks:
                    subtask_start_date = None
                    subtask_first_status_change_action = TaskAction.objects.filter(
                        task__id=task.id,
                        remark__icontains=f"Sub Task '{subtask.task_topic}' status has been updated"
                    ).order_by('created_at').first()
                    if subtask_first_status_change_action:
                        subtask_start_date = subtask_first_status_change_action.created_at
                    
                    subtask_hierarchy_instance = TaskHierarchy.objects.create(
                        created_by=subtask.created_by,
                        checklist=task.checklist,
                        task_topic=subtask.task_topic,
                        due_date=subtask.due_date,
                        task_description=subtask.task_description,
                        urgent_status=subtask.urgent_status,
                        status=subtask.status,
                        sequence=task.sequence,  # Assuming subtask follows the same sequence
                        is_personal=task.is_personal,
                        reopened_count=subtask.reopened_count,
                        inTrash=subtask.inTrash,
                        trashed_with=subtask.trashed_with,
                        project_file_name=task.project_file_name,
                        start_date=subtask_start_date if subtask_start_date else subtask.start_date,
                        end_date=subtask.end_date,
                        parent=task_hierarchy_instance,
                        task_level=1
                    )
                    subtask_hierarchy_instance.assign_to.set(subtask.assign_to.all())

                    # Handle SubTaskChild
                    subtask_children = SubTaskChild.objects.filter(subtasks=subtask, inTrash = False)
                    for subtask_child in subtask_children:
                        
                        subtask_child_start_date = None
                        subtask_child_first_status_change_action = TaskAction.objects.filter(
                            task__id=task.id,
                            remark__icontains=f"Sub Task child'{subtask_child.task_topic}' status has been updated"
                        ).order_by('created_at').first()
                        if subtask_child_first_status_change_action:
                            subtask_child_start_date = subtask_child_first_status_change_action.created_at
                            
                            
                        TaskHierarchy.objects.create(
                            created_by=subtask_child.created_by,
                            checklist=task.checklist,
                            task_topic=subtask_child.task_topic,
                            due_date=subtask_child.due_date,
                            task_description=subtask_child.task_description,
                            urgent_status=subtask_child.urgent_status,
                            status=subtask_child.status,
                            sequence=task.sequence,  # Assuming subtask follows the same sequence
                            is_personal=task.is_personal,
                            reopened_count=subtask_child.reopened_count,
                            inTrash=subtask_child.inTrash,
                            trashed_with=subtask_child.trashed_with,
                            project_file_name=task.project_file_name,
                            start_date=subtask_child_start_date if subtask_child_start_date else subtask_child.start_date,
                            end_date=subtask_child.end_date,
                            parent=subtask_hierarchy_instance,
                            task_level=2
                        ).assign_to.set(subtask_child.assign_to.all())

        return {
            "success": True,
            "message": "Tasks copied to TaskHierarchy successfully."
        }

    except Exception as e:
        print("Error in copy_tasks_to_task_hierarchy:", str(e))
        return {
            "success": False,
            "message": str(e)
        }