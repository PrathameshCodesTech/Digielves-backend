
import requests
from requests.auth import HTTPBasicAuth
import json
from django.conf import settings




client_id = "33d46bb8-945b-4c07-bf6c-74f89c263b23"
client_secret = "jQd8Q~_GsRrLZoBULCcHe5Rx1wxpzDivMdNWQc0J"
tenant_id = "ad2b1ce8-b182-443b-bc9c-1db30df9f99e"
resource = "https://graph.microsoft.com/"

team_api_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/token'
auth_data = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret,
    "resource": resource
}


def get_teams_access_token():
    print("yah---------------")
    try:

        auth_response = requests.post(team_api_url, data=auth_data)
        print("------------------------------------------hhhhhhhh--hh")
        print(auth_response)
        auth_response_data = auth_response.json()
        access_token = auth_response_data["access_token"]
        print("---------------------------------------h-hhhhhhhhhhhhhhhhh")
        print(access_token)
        
        
        return access_token
    except Exception as e:
        print(e)
        return None 

#    if response.status_code == 200:
#        response_data = response.json()
#        access_token = response_data.get('access_token')
#        settings.ZOOM_ACCESS_TOKEN = access_token
#        return access_token
#    else:
#        # Handle error cases here
#        print("error in zoom utils--------")
#        return None