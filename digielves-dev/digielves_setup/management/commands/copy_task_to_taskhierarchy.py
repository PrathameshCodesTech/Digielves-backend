# notifications/management/commands/check_overdue_tasks.py
from django.core.management.base import BaseCommand

import logging

from digielves_setup.cron_task.copy_tasks_to_taskhierachy import copy_tasks_to_task_hierarchy


logger = logging.getLogger('api_hits')

class Command(BaseCommand):
    help = 'Check and add notifications for appointments'

    def handle(self, *args, **options):
        try:
            copy_tasks_to_task_hierarchy()
            self.stdout.write(self.style.SUCCESS('Successfully copied.'))
        except Exception as e:
            
            self.stderr.write(self.style.ERROR(f'Error during cron job execution: {e}'))
