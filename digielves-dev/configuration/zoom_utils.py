# zoom_util.py

import requests
from requests.auth import HTTPBasicAuth
import json
from django.conf import settings

zoom_api_url = 'https://zoom.us/oauth/token'
grant_type = 'account_credentials'
account_id = 'd6UPxnmvSKq5dXnHBVM3ag'


zoom_username = '7n1UDqe7QOESjU0WV8J3Q'
zoom_password = '7J0KZLG4IF5DjZ1tEFInOv0BKtEAKsUt'

def get_zoom_access_token():
    print("getting zoom tokens----------------")
#    if hasattr(settings, 'ZOOM_ACCESS_TOKEN') and settings.ZOOM_ACCESS_TOKEN:
#
#        return settings.ZOOM_ACCESS_TOKEN


    params = {
              'grant_type': 'account_credentials',
              'account_id': 'd6UPxnmvSKq5dXnHBVM3ag',
          }
    
    # If the access token is not cached, fetch it from Zoom
    basic_auth = HTTPBasicAuth(zoom_username, zoom_password)
    

    response = requests.post(zoom_api_url, params=params, auth=basic_auth)

    if response.status_code == 200:
        response_data = response.json()
        access_token = response_data.get('access_token')
        settings.ZOOM_ACCESS_TOKEN = access_token
        
        # print(access_token)
        return access_token
    else:
        # Handle error cases here
        print("error in zoom utils--------")
        return None
