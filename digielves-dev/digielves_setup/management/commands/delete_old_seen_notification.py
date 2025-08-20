# notifications/management/commands/check_overdue_tasks.py
from django.core.management.base import BaseCommand

import logging

from digielves_setup.cron_task.check_notification_seen import delete_old_seen_notifications



logger = logging.getLogger('api_hits')

class Command(BaseCommand):
    help = 'Check notifications'

    def handle(self, *args, **options):
        try:
            delete_old_seen_notifications()
            self.stdout.write(self.style.SUCCESS('Successfully deleted notification.'))
        except Exception as e:
            
            self.stderr.write(self.style.ERROR(f'Error during cron job execution: {e}'))
