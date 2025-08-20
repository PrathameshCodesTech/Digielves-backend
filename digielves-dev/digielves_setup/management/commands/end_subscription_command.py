# notifications/management/commands/check_overdue_tasks.py
from django.core.management.base import BaseCommand
from digielves_setup.cron_task.delete_task import check_and_delete_tasks

import logging

from digielves_setup.cron_task.end_subscription import check_end_of_subscription


logger = logging.getLogger('api_hits')

class Command(BaseCommand):
    help = 'Check and add notifications for end of subscription'

    def handle(self, *args, **options):
        try:
            check_end_of_subscription()
            self.stdout.write(self.style.SUCCESS('Successfully checked subscription.'))
        except Exception as e:
            
            self.stderr.write(self.style.ERROR(f'Error during cron job execution: {e}'))
