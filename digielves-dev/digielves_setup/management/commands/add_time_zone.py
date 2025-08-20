# from django.core.management.base import BaseCommand

# from digielves_setup.models import Tasks
# from django.utils import timezone
# from datetime import datetime

# class Command(BaseCommand):
#     help = 'Copies values from due_date to due_datee field in Tasks model'

#     def handle(self, *args, **options):
#         tasks = Tasks.objects.all()
#         for task in tasks:
#             if task.due_date:
#                 # Parse the due_date string into a datetime object
#                 due_date_datetime = datetime.strptime(task.due_date, "%Y-%m-%dT%H:%M")

#                 # Convert the datetime object to the project's timezone
#                 due_date_datetime_utc = timezone.make_aware(due_date_datetime, timezone=timezone.utc)
#                 due_date_datetime_local = due_date_datetime_utc.astimezone(timezone.get_current_timezone())

#                 task.due_datee = due_date_datetime_local
#                 task.save()

#         self.stdout.write(self.style.SUCCESS('Values copied successfully'))
