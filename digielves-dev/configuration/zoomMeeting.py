from configuration.zoom_utils import get_zoom_access_token
import requests
import json
import os
import uuid
from django.http import JsonResponse



def create_zoom_meeting(agenda,start_time,users):
    bearer_token = get_zoom_access_token()
    print("---dddddddd-------xxxx---create zoom")
    
    print(bearer_token)
    
    
    url = 'https://api.zoom.us/v2/users/me/meetings'

    headers = {
        'Authorization': f'Bearer {bearer_token}',
        'Content-Type': 'application/json',
    }
    print(headers)
    print(users)
    
    data = {
        'agenda': agenda,
        'default_password': False,
        'duration': 60,
        'password': '123456',
        'pre_schedule': False,
        'settings': {
            'auto_recording': 'cloud',
            'host_video': True,
            'jbh_time': 0,
            'join_before_host': True,
            'meeting_authentication': False,
            'meeting_invitees': users,
            'mute_upon_entry': False,
            'waiting_room': False,

            'continuous_meeting_chat': {
                'enable': True,
                'auto_add_invited_external_users': True,
            },


        },
        'start_time': start_time,
        'timezone': 'Asia/Kolkata',
        'topic': agenda,
        'type': 2,
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    print("fererfrg----------------------")
    print(response.status_code)  
    if response.status_code == 201:
        response_data = response.json()

        return response_data.get('join_url'), response_data.get('uuid'), response_data.get('id')
    else:
        return 0,0,0


