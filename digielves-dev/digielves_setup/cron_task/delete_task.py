
from django.utils import timezone
from digielves_setup.models import ChecklistTasks, TaskChecklist, TaskHierarchy, Tasks
from django.db.models import Q
from datetime import timedelta

def check_and_delete_tasks():
    thirty_days_ago = timezone.now() - timedelta(days=30)

    conditions = [
        Q(inTrash=True),
        Q(updated_at__lt=thirty_days_ago),
    ]

    tasks_to_delete = TaskHierarchy.objects.filter(*conditions)
 
    tasks_to_delete.delete()



# from django.utils import timezone

# from digielves_setup.models import ChecklistTasks, TaskChecklist, Tasks
# from django.db.models import Q
# from datetime import timedelta

# def check_and_delete_tasks():
#     current_date = timezone.now()
#     thirty_days_ago = current_date - timedelta(days=30)
#     print(thirty_days_ago)

#     over_tasks = Tasks.objects.filter(
#         Q(inTrash=True) &
#         Q(updated_at__lt=thirty_days_ago)
#     )
    
#     over_checklist = TaskChecklist.objects.filter(
#          Q(inTrash=True) &
#         Q(updated_at__lt=thirty_days_ago)&
#         Q(trashed_with="Manually")
#     )
#     over_checklist_task = ChecklistTasks.objects.filter(
#          Q(inTrash=True) &
#         Q(updated_at__lt=thirty_days_ago)&
#         Q(trashed_with="Manually")
#     )

    


#     if over_tasks.exists():
#         over_tasks.delete()
#     else:
#         pass

#     if over_checklist.exists():
#         over_checklist.delete()
#     else:
#         pass
    
#     if over_checklist_task.exists():
#         over_checklist_task.delete()
#     else:
#         pass

   
    
  
        


