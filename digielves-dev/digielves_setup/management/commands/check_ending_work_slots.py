# notifications/management/commands/check_overdue_tasks.py
from django.core.management.base import BaseCommand

from digielves_setup.cron_task.find_ending_work_slots import get_users_with_ending_slots
import logging


logger = logging.getLogger('api_hits')

class Command(BaseCommand):
    help = 'Check and add notifications for appointments'

    def handle(self, *args, **options):
        try:
            logger.info(f"started Cron API hit cccccc")
            get_users_with_ending_slots()
            self.stdout.write(self.style.SUCCESS('Successfully checked .'))
        except Exception as e:
            logger.info(f"Cron API hit cccccc")
            self.stderr.write(self.style.ERROR(f'Error during cron job execution: {e}'))