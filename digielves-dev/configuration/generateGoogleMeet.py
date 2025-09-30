import requests
import json
import pyshorteners



import requests
import json
import pyshorteners

# Set up your Google API credentials
CLIENT_ID = '53662667789-v0050enl3d22u8v3eb579ttcte9rfj26.apps.googleusercontent.com'
CLIENT_SECRET = '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'
REFRESH_TOKEN = '1//049RR-JcxG2dTCgYIARAAGAQSNwF-L9Ir570MyNH2VCuTbGtJjMIoxyUvmSjxFoHJ6wrj0WdJ1dABpzWShswzyX7bPRwJ4Kbv4B4'
API_KEY = 'AIzaSyBmLKeAlNhgA-Y25NrXSuunNj4cPkAH_AQ'
# AUTH_TOKEN = 'ya29.a0AWY7CknGAjCMN64EWXM-z_PIa8NSvYIbQJI0R2IsJFZ_9UiNoIt5ygYCl68BcyKWV3iBLbj0Bb_nCaymeAQlruztXtC4I4esMQfAy2weU5r2OA3uYKAkwDRUv8sw25luB69eACVhsQ5UiOl6yeSO6S_LorOHKGhKaCgYKASASARISFQG1tDrpTyzQkWUQ-JtzDdjZrpsXOA0167'


# Endpoint for token refresh  
token_refresh_url = 'https://oauth2.googleapis.com/token'

AUTH_TOKEN = None

def refresh_access_token():
    # Prepare the refresh token request payload  
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }

    # Send the refresh token request
    
    # response = requests.post(token_refresh_url,  data=json.dumps(meeting_parameters))
    # response_data = response.json()
    
    

    response = requests.post(token_refresh_url, data=payload) 
    response_data = response.json()
    print('c'*50)
    # print(response_data)

    

    # Extract the new access token from the response
    new_access_token = response_data.get('access_token')

    # Update the stored access token with the new value
    update_access_token(new_access_token)

    return new_access_token

def update_access_token(new_access_token):
    global AUTH_TOKEN
    AUTH_TOKEN = new_access_token

def get_stored_access_token():
    global AUTH_TOKEN
    return AUTH_TOKEN

def generateMeeting(start_time):
    global AUTH_TOKEN

    # Get the stored access token
    AUTH_TOKEN = get_stored_access_token()

    # Check if the access token is valid or expired
    if not AUTH_TOKEN:
        AUTH_TOKEN = refresh_access_token()

    # Make the API request using the access token
    headers = {
        'Authorization': f'Bearer {AUTH_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    
    meeting_parameters = {
        'title': 'My Meeting',
        'start': {
            'dateTime': '2023-05-25T09:00:00',
            'timeZone': 'Asia/Kolkata'
        }, 

        'end': {
            'dateTime': '2023-05-25T10:00:00',
            'timeZone': 'Asia/Kolkata'
        },
        'conferenceData': {
            'createRequest': {
                'requestId': 'abcd1234'
            }
        }
    }

    # Create the meeting using the Google Calendar API
    headers = {
        'Authorization': f'Bearer {AUTH_TOKEN}',
        'Content-Type': 'application/json'
    }
    response = requests.get(f'https://www.googleapis.com/calendar/v3/calendars/primary/events?key={API_KEY}', headers=headers)

    
    
    
    
# #     if response.status_code == 401:
# #         AUTH_TOKEN = refresh_access_token()
# #         headers['Authorization'] = f'Bearer {AUTH_TOKEN}'
# #         response = requests.get(f'https://www.googleapis.com/calendar/v3/calendars/primary/events?key={API_KEY}', headers=headers)
# #         return("shortened_url")

# #     if response.status_code == 200:
# #         data = response.json()
# #         print("API Response:", data)
# #         print(AUTH_TOKEN)

# #         # Extract the Google Meet URL from the API response
# #         items = data.get('items', [])
# #         shortened_url = data['items'][len(data['items'])-1]['conferenceData']['entryPoints'][0]['uri']  
       
# #         return(shortened_url)
        
# # print(generateMeeting("ewer"))





# import datetime
# from googleapiclient.discovery import build
# from google.oauth2 import service_account

# # Set up credentials
# credentials = service_account.Credentials.from_service_account_file('./credentials.json')
# scopes = ['https://www.googleapis.com/auth/calendar']
# service = build('calendar', 'v3', credentials=credentials)

# # Create a Google Meet event
# event = {
#     'summary': 'Meeting Title',
#     'start': {
#         'dateTime': '2023-06-04T09:00:00',  # Set the start date and time
#         'timeZone': 'Asia/Kolkata',  # Provide the time zone
#     },
#     'end': {
#         'dateTime': '2023-06-04T10:00:00',  # Set the end date and time
#         'timeZone': 'Asia/Kolkata',  # Provide the time zone
#     },
#     'conferenceData': {
#         'createRequest': {
#             'requestId': 'random-string',
#             'conferenceSolutionKey': {
#                 'type': 'hangoutsChat',
#             }
#         },
#     },
# }

# # Insert the event
# event = service.events().insert(calendarId='primary', body=event, conferenceDataVersion=1).execute()

# # Retrieve the Google Meet link
# meeting_link = event['conferenceData']['entryPoints'][0]['uri']
# print('Google Meet Link:', meeting_link)




