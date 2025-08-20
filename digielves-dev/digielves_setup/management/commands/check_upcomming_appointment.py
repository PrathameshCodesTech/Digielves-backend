# notifications/management/commands/check_overdue_tasks.py
from django.core.management.base import BaseCommand

from digielves_setup.cron_task.check_overdue import check_overdue_tasks
from digielves_setup.cron_task.upcoming_appointments import check_upcoming_appointments
import logging


logger = logging.getLogger('api_hits')

class Command(BaseCommand):
    help = 'Check and add notifications for appointments'

    def handle(self, *args, **options):
        try:
            logger.info(f"started Cron API hit cccccc")
            check_upcoming_appointments()
            self.stdout.write(self.style.SUCCESS('Successfully checked appointments and added notifications for appointments.'))
        except Exception as e:
            logger.info(f"Cron API hit cccccc")
            self.stderr.write(self.style.ERROR(f'Error during cron job execution: {e}'))
