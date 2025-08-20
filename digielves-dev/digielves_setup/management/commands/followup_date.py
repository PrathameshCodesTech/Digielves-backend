# notifications/management/commands/check_overdue_tasks.py
from django.core.management.base import BaseCommand

import logging

from digielves_setup.cron_task.next_followup_date import check_next_followup_date


logger = logging.getLogger('api_hits')

class Command(BaseCommand):
    help = 'Check and add notifications for end of subscription'

    def handle(self, *args, **options):
        try:
            check_next_followup_date()
            self.stdout.write(self.style.SUCCESS('Successfully checked follow up.'))
        except Exception as e:
            
            self.stderr.write(self.style.ERROR(f'Error during cron job execution: {e}'))
