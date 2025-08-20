# notifications/management/commands/check_overdue_tasks.py
from django.core.management.base import BaseCommand

import logging

from digielves_setup.cron_task.check_nd_update_meeting_status import check_and_update_meeting_status


logger = logging.getLogger('api_hits')

class Command(BaseCommand):
    help = 'Check and add notifications for appointments'

    def handle(self, *args, **options):
        try:
            check_and_update_meeting_status()
            self.stdout.write(self.style.SUCCESS('Successfully checked status .'))
        except Exception as e:
            logger.info(f"Cron API hit cccccc")
            self.stderr.write(self.style.ERROR(f'Error during cron job execution: {e}'))