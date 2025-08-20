
from django.http import JsonResponse
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
import jwt
import datetime
from configuration import settings

class ZoomMeetViewset(viewsets.ModelViewSet):
    


    def create_zoom_meeting(request):
        # Set up API credentials
        client_id = settings.ZOOM_CLIENT_ID
        client_secret = settings.ZOOM_CLIENT_SECRET

        # Obtain an OAuth access token (if using OAuth for user authentication)
        # Follow Zoom's OAuth flow to obtain this token

        # Create the meeting using the access token
        create_meeting_url = 'https://api.zoom.us/v2/users/me/meetings'
        headers = {
            'Authorization': f'Bearer {access_token}',  # Replace with your access token
            'Content-Type': 'application/json',
        }
        meeting_data = {
            "topic": "My Zoom Meeting",
            "type": 2,  # Scheduled meeting
            "start_time": "2023-09-01T12:00:00Z",
            "duration": 60,  # Duration in minutes
        }

        response = requests.post(create_meeting_url, json=meeting_data, headers=headers)

        if response.status_code == 201:
            return JsonResponse({'message': 'Zoom meeting created successfully'})
        else:
            return JsonResponse({'error': 'Failed to create Zoom meeting'}, status=response.status_code)
