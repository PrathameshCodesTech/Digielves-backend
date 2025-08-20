# notifications/management/commands/check_overdue_tasks.py
from django.core.management.base import BaseCommand

from digielves_setup.cron_task.check_overdue import check_overdue_tasks
from digielves_setup.cron_task.check_server_available import check_server
from digielves_setup.cron_task.upcoming_appointments import check_upcoming_appointments


class Command(BaseCommand):

    def handle(self, *args, **options):
        check_server()
        
        self.stdout.write(self.style.SUCCESS('Successfully checked .'))
