from configuration.zoom_utils import get_zoom_access_token
import requests
import json
import os
import uuid
from django.http import JsonResponse
from configuration.team_utils import get_teams_access_token


def create_teams_meeting(agenda,start_time,users):
#    bearer_tokens = "eyJ0eXAiOiJKV1QiLCJub25jZSI6Imt5a1dlZzhtYXpZZEtGZDRKakI3eGVFNzlVZ0hwTFpBcjd1MUV4bWx5aGMiLCJhbGciOiJSUzI1NiIsIng1dCI6IjlHbW55RlBraGMzaE91UjIybXZTdmduTG83WSIsImtpZCI6IjlHbW55RlBraGMzaE91UjIybXZTdmduTG83WSJ9.eyJhdWQiOiIwMDAwMDAwMy0wMDAwLTAwMDAtYzAwMC0wMDAwMDAwMDAwMDAiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9hZDJiMWNlOC1iMTgyLTQ0M2ItYmM5Yy0xZGIzMGRmOWY5OWUvIiwiaWF0IjoxNjk3NDYwODM4LCJuYmYiOjE2OTc0NjA4MzgsImV4cCI6MTY5NzU0NzUzOCwiYWNjdCI6MCwiYWNyIjoiMSIsImFpbyI6IkFWUUFxLzhVQUFBQUZLU3FSd3RWcGtkRkdXbjNUdWZsWHB5QjhkRWUwQXFUb1F1c1lDZlA5SEIyR1RFSmwrcm56OXIyNSs5SFVteTFrY0paYzdFaVRocUhQN0ZiQXo1R1IwcVZ1T1pxTXBUdWZXekNGUWxyYjNJPSIsImFtciI6WyJwd2QiLCJyc2EiLCJtZmEiXSwiYXBwX2Rpc3BsYXluYW1lIjoiR3JhcGggRXhwbG9yZXIiLCJhcHBpZCI6ImRlOGJjOGI1LWQ5ZjktNDhiMS1hOGFkLWI3NDhkYTcyNTA2NCIsImFwcGlkYWNyIjoiMCIsImRldmljZWlkIjoiOWVkZTIxNDItN2RmNC00YTZjLWJmZTMtN2NiYTQ4NmNkZTQzIiwiZmFtaWx5X25hbWUiOiJLaHVsZSIsImdpdmVuX25hbWUiOiJBZGl0eWEiLCJpZHR5cCI6InVzZXIiLCJpcGFkZHIiOiIxMDMuMTY3LjI0NS4yMDQiLCJuYW1lIjoiQWRpdHlhIEtodWxlIiwib2lkIjoiZjg5Zjk0MTgtYTcyZi00ZDI4LWEwYTctMzNkZGNkMGZjMzI1IiwicGxhdGYiOiIzIiwicHVpZCI6IjEwMDMyMDAzMDNCNjNCMkQiLCJyaCI6IjAuQVQwQTZCd3JyWUt4TzBTOG5CMnpEZm41bmdNQUFBQUFBQUFBd0FBQUFBQUFBQUNoQUFVLiIsInNjcCI6IkNhbGVuZGFycy5SZWFkLlNoYXJlZCBDYWxlbmRhcnMuUmVhZFdyaXRlIENhbGVuZGFycy5SZWFkV3JpdGUuU2hhcmVkIERpcmVjdG9yeS5SZWFkLkFsbCBEaXJlY3RvcnkuUmVhZFdyaXRlLkFsbCBGaWxlcy5SZWFkIEZpbGVzLlJlYWQuQWxsIEZpbGVzLlJlYWRXcml0ZSBGaWxlcy5SZWFkV3JpdGUuQWxsIE9ubGluZU1lZXRpbmdBcnRpZmFjdC5SZWFkLkFsbCBPbmxpbmVNZWV0aW5nUmVjb3JkaW5nLlJlYWQuQWxsIE9ubGluZU1lZXRpbmdzLlJlYWQgT25saW5lTWVldGluZ3MuUmVhZFdyaXRlIE9ubGluZU1lZXRpbmdUcmFuc2NyaXB0LlJlYWQuQWxsIG9wZW5pZCBwcm9maWxlIFNpdGVzLlJlYWQuQWxsIFNpdGVzLlJlYWRXcml0ZS5BbGwgVGVhbXNBY3Rpdml0eS5SZWFkIFRlYW1zQWN0aXZpdHkuU2VuZCBVc2VyLlJlYWQgVXNlckFjdGl2aXR5LlJlYWRXcml0ZS5DcmVhdGVkQnlBcHAgZW1haWwiLCJzaWduaW5fc3RhdGUiOlsia21zaSJdLCJzdWIiOiJRWlZyNlZ6Z0tYSjdHMU1LNzN1Q2pieDQ4dXE0cXpSLXV2MUZGNEhTSC04IiwidGVuYW50X3JlZ2lvbl9zY29wZSI6IkFTIiwidGlkIjoiYWQyYjFjZTgtYjE4Mi00NDNiLWJjOWMtMWRiMzBkZjlmOTllIiwidW5pcXVlX25hbWUiOiJBZGl0eWFraHVsZUBPcmRpbmV0U29sdXRpb25zMTUub25taWNyb3NvZnQuY29tIiwidXBuIjoiQWRpdHlha2h1bGVAT3JkaW5ldFNvbHV0aW9uczE1Lm9ubWljcm9zb2Z0LmNvbSIsInV0aSI6IkVfTlJEaEZlU2tLVUQzNlBiYmtHQUEiLCJ2ZXIiOiIxLjAiLCJ3aWRzIjpbIjYyZTkwMzk0LTY5ZjUtNDIzNy05MTkwLTAxMjE3NzE0NWUxMCIsImI3OWZiZjRkLTNlZjktNDY4OS04MTQzLTc2YjE5NGU4NTUwOSJdLCJ4bXNfY2MiOlsiQ1AxIl0sInhtc19zc20iOiIxIiwieG1zX3N0Ijp7InN1YiI6InRSMkY5bmxVWWhNQXFsQVhGV2tFYTZQVzBqMHlZTGhYWmt4UUVxUTJOQ0EifSwieG1zX3RjZHQiOjE2OTcxMTM1NTV9.VGCa_Z_w76XyIfi4PEZJxUMsxDbwCeZbnRTnECWFqOLiRmnTa03zhvlopl4mNPQDPmz3HFXEJT9ntW6f4FxZEJedXnRUZhaEZ0Ir0wiaYZFG4Payq9fed8jzI2JyIGnjWODBdkpGJSkRqohSDZulMwliOKmm3y3pcNCs3EbvMSCJ2W8HBTvuUgp9uGr6DT6v7DL_JRx6Hyy0lTY9ss_rP0nZpOATP50vFRR_HSft8io0yGtMku1TY029sG54lIXXyjQ07CW04633mvcg5adCzvknFXEK0TVOUhdZIxdqMSJXJEB3vBRLk8Ghao3T8-GEuIsDsqgC1nvNfgmp1hC-gQ"
    print("-------------create teams")
    
    #print(bearer_token)
    bearer_tokens=get_teams_access_token()
    print("-------------------------------------------------hey-------------")
    #print(bearer_tokens)
    
    url = 'https://graph.microsoft.com/v1.0/users/f89f9418-a72f-4d28-a0a7-33ddcd0fc325/events'
    getMeetingIDUrl = "https://graph.microsoft.com/v1.0/users/f89f9418-a72f-4d28-a0a7-33ddcd0fc325/onlineMeetings?$filter=JoinWebUrl%20eq%20"
    enableRecordingUrl = "https://graph.microsoft.com/v1.0/users/f89f9418-a72f-4d28-a0a7-33ddcd0fc325/onlineMeetings/"
    headers = {
        'Authorization': f'Bearer {bearer_tokens}',
        'Content-Type': 'application/json',
    }
    #print(headers)

    data = {
        "subject":agenda ,
        "start": {
            "dateTime": "2023-10-15T15:57:33.195Z",
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": "2023-10-20T15:57:33.195Z",
            "timeZone": "UTC"
        },
        "isOnlineMeeting": True
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    print("fererfrg")
    print(response.status_code)  
    if response.status_code == 201:
        response_data = response.json()
        print("res---data")
        print(response_data)
        #print(response_data.keys())

        meeting_url =  response_data['onlineMeeting']['joinUrl']
        
        getMeetingIDUrl += "'"  + str(meeting_url) + "'"
        meetingID = requests.get(getMeetingIDUrl , headers=headers)
        print(meetingID.status_code)
        #print(meetingID.json()['value'][0]['id'])
        
        enableRecordingUrl += meetingID.json()['value'][0]['id']
        recording = {
        "recordAutomatically": True
        }
        recording = requests.patch(enableRecordingUrl, headers=headers,  data=json.dumps(recording ))

        return meeting_url, meetingID.json()['value'][0]['id'], meetingID.json()['value'][0]['id']
    else:
        return 0,0,0



