# notifications/management/commands/check_overdue_tasks.py
from django.core.management.base import BaseCommand

from digielves_setup.cron_task.check_overdue import check_overdue_tasks
from digielves_setup.cron_task.upcoming_appointments import check_upcoming_appointments
from digielves_setup.cron_task.upcoming_meeting import check_upcoming_meeting


class Command(BaseCommand):
    help = 'Check and add notifications for overdue meeting'

    def handle(self, *args, **options):
        check_upcoming_meeting()
        
        self.stdout.write(self.style.SUCCESS('Successfully checked and added notifications for overdue meeting.'))
