# notifications/management/commands/check_overdue_tasks.py
from django.core.management.base import BaseCommand
from digielves_setup.cron_task.delete_task import check_and_delete_tasks

import logging


logger = logging.getLogger('api_hits')

class Command(BaseCommand):
    help = 'Check and add notifications for appointments'

    def handle(self, *args, **options):
        try:
            check_and_delete_tasks()
            self.stdout.write(self.style.SUCCESS('Successfully checked and Delete Task.'))
        except Exception as e:
            
            self.stderr.write(self.style.ERROR(f'Error during cron job execution: {e}'))
