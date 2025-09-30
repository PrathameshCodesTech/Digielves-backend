import requests
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView
from django.http import JsonResponse

@permission_classes((AllowAny, ))
class GithubSocialAuthView(APIView):
    def post(self, request):
        #user_object=User()
        code = request.data.get('code')
        org_id=request.data.get('org_id')
        token=request.data.get('token')
        print(code)
        print(org_id)
        print(token)
        client_id = '3a4073e7808e53bbdfa3'
        client_secret = '45d1cd25c96d0f57ccab2e9113d3ba9bd6c45bdd'
        access_token_url = 'https://github.com/login/oauth/access_token'
        user_url = 'https://api.github.com/user'        

        # Exchange the code for an access token
        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code
        }
        response = requests.post(access_token_url, data=payload)
        

        if response.status_code == 200:
            print("got res----")
            # Parse the response to extract the access token
            access_token = response.text.split('&')[0].split('=')[1]
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            user_repos_url = 'https://api.github.com/user/repos'
            response = requests.get(user_repos_url, headers=headers)
            response1 = requests.get(user_url, headers=headers)
            print("shivay")
            print(response1)
            try:
              emails_url = 'https://api.github.com/user/emails'
              email_response = requests.get(emails_url, headers={'Authorization': f'Bearer {access_token}'})
              if email_response.status_code == 200:
                  emails = email_response.json()
                  print("-------hum tum kitne pass")
                  print(emails)
                  
                  emails = email_response.json()
                  primary_email = None

                  
                  for email in emails:
                      if email['primary']:
                          primary_email = email['email']
                          break
                  if primary_email:
                      return JsonResponse({
                            "success": True,
                            "status": status.HTTP_200_OK, 
                            "message": "Got email",
                            "email": primary_email
                            })
                  else:
                      return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Email Not found",
                            })
                    
                      
                        
                  
            except Exception as e:
                print("except----------")
                print(e)
                return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Getting Problem with email",
                            "error":str(e)
                            })
            
            

        
        return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Error",
                            "error":str(e)
                            })
