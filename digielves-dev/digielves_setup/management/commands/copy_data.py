from django.core.management.base import BaseCommand

from digielves_setup.models import ChecklistTasks, Tasks
from django.utils import timezone as NewTimeZOne
from datetime import datetime
import pytz
class Command(BaseCommand):
    help = 'Copies values from due_date to due_datee field in Tasks model'

    def handle(self, *args, **options):
        tasks = Tasks.objects.all()
        # Initialize a counter to keep track of the number of tasks processed
        counter = 0
        # Define the IST timezone
        ist_tz = pytz.timezone('Asia/Kolkata')
        for task in tasks:
            print(task.id)
            if task.due_date:  # Check if due_date is not None and counter is less than 2
                due_date_ist = task.due_date - NewTimeZOne.timedelta(hours=5, minutes=30)
            
                # Assign due_date_ist to due_date_new
                task.due_date_new = due_date_ist
                
                # Save the task
                task.save()
                
            
                            
               

                
            

        self.stdout.write(self.style.SUCCESS('Values copied successfully'))
