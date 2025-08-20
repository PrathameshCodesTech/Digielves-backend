from django.utils import timezone
from datetime import timedelta

from digielves_setup.models import Meettings

def check_and_update_meeting_status():
    try:
        time_threshold = timezone.now() - timedelta(minutes=20)
        
        meetings = Meettings.objects.filter(meet_start_time__lte=time_threshold, status_complete=False)
        
        for meeting in meetings:
            meeting.status_complete = True
            meeting.save()
    
    except Exception as e:
        print(f"Error in check_and_update_meeting_status: {e}")

