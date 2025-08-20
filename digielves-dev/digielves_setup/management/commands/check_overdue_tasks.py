# notifications/management/commands/check_overdue_tasks.py
from django.core.management.base import BaseCommand

from digielves_setup.cron_task.check_overdue import check_overdue_tasks
from digielves_setup.cron_task.upcoming_appointments import check_upcoming_appointments


class Command(BaseCommand):
    help = 'Check and add notifications for overdue tasks'

    def handle(self, *args, **options):
        check_overdue_tasks()
        
        self.stdout.write(self.style.SUCCESS('Successfully checked and added notifications for overdue tasks.'))
