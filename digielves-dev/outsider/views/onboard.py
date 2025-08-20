import json
from configuration.gzipCompression import compress


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from configuration.userCreationToken import generate_random_string


from digielves_setup.models import EmployeePersonalDetails, Notification, OutsiderUser, User, UserCreation, notification_handler
from digielves_setup.send_emails.email_conf.send_outsider_onboard_link import sendOutsiderOnBoardLink

from outsider.seriallizer.onboard_seriallizers import OutsiderUserRegistraionSerializer
from rest_framework import viewsets
from rest_framework import status
import threading
import csv
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
import datetime
from rest_framework.permissions import  IsAuthenticated ,AllowAny
import bcrypt
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.utils import timezone
class OutsiderUserCreationClass(viewsets.ModelViewSet):

    # authentication_classes = [JWTAuthenticationUser]
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]

    # throttle_classes = [AnonRateThrottle,UserRateThrottle]
    # serializer_class= UpdateUserCreationSerializers
    

    @csrf_exempt
    def createOutsiderUser(self, request):
        try:
            added_by_id = request.POST.get('added_by')
            # Check if the user with the given email already exists
            existing_user_creation = UserCreation.objects.filter(email=request.data['email']).first()
            print("🐍 File: views/onboard.py | Line: 41 | createOutsiderUser ~ existing_user_creation",existing_user_creation)
            existing_user = OutsiderUser.objects.filter(email=request.data['email']).first()
            print("🐍 File: views/onboard.py | Line: 42 | createOutsiderUser ~ existing_user",existing_user)
            if existing_user or existing_user_creation:
                existing_user_added_by_same = OutsiderUser.objects.filter(email=request.data['email'],added_by =  added_by_id).first()
                if existing_user_added_by_same:
                    return JsonResponse({
                        "success": False,
                        "status": 122,
                        "message": "It seems that username is already in use. Please choose a different username to continue. ",
                    })
                else:
                    
                    existing_user.secondary_adders.add(added_by_id)
                    existing_user.save()
                    
                    return JsonResponse({
                        "success": True,
                        "status": 123,
                        "message": "Outsider User Added"
                        
                    }, status=201)
            
            
            
            email = request.POST.get('email')

            if not added_by_id or not email:
                return JsonResponse({
                    "success": False,
                    "status": "Missing required fields"
                }, status=400)

            try:
                added_by_user = User.objects.get(id=added_by_id)
            except User.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": "Added by user not found"
                }, status=404)
                    
            token = generate_random_string(52)
            
            employee_organization = EmployeePersonalDetails.objects.get(user_id = added_by_id)
            
            outsider_user = OutsiderUser(
                added_by=added_by_user,
                organization_id = employee_organization.organization_id.id,
                email=email,
                token=token,
            )
            outsider_user.save()
            
            
            
            t = threading.Thread(target=thread_to_send_outsider_invitation, args=(email,str(token)))
            t.setDaemon(True) 
            t.start() 
                    
            return JsonResponse({
                "success": True,
                "status": "Outsider user created successfully",
                "data": {
                    "id": outsider_user.id,
                    "email": outsider_user.email,
                    "token": outsider_user.token,
                }
            }, status=201)
    
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error.",
                "errors": str(e)
            })
            
    @csrf_exempt
    def OutsideUserRegistraion(self,request):
        user_object=User()
        
        with open('useful.csv') as f:
            reader = csv.reader(f)
            next(reader)      # <- skip the header row
            for row in reader:
                csv_key = row[0]
                
        csv_key = csv_key.replace('RUSH','')
        csv_key = csv_key.replace('ISHK','')

        try:
            try:
                
                outsider_user = OutsiderUser.objects.get(token = request.data['token'], email = request.data['email'] )
            except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": 121, 
                        "message": "No user found with the provided invitation token and email.",
                        })      
     
            #, processed = 0
            user = OutsiderUserRegistraionSerializer(user_object,data=request.data)


            if user.is_valid(raise_exception=True):
                try:    
                    
                    response = user.save()
                    
                    outsider_user.processed = 1
                    outsider_user.related_id = User.objects.get(id=response.id)
                    
                    outsider_user.save()
                    
                    token= RefreshToken.for_user(User.objects.get(id=response.id))
                    
                    token_json = {'access' :{} , 'refresh' : {}}
                    token_json['access']['token'] = str(token.access_token) 
                    token_json['refresh']['token'] = str(token)

                    
                    decoded_token = RefreshToken(str(token)).payload
                    expiry_time = decoded_token["exp"]
                    # Convert the expiry time to a datetime object
                    token_json['refresh']['expiry'] = datetime.datetime.fromtimestamp(expiry_time)
                    
                    
                    decoded_token = AccessToken(str(token.access_token)).payload
                    expiry_time = decoded_token["exp"]
                    # Convert the expiry time to a datetime object
                    token_json['access']['expiry'] = datetime.datetime.fromtimestamp(expiry_time)
                    
                    
                    return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User created successfully",
                    'token': token_json,

                    "data": {
                        'user_id' : user_object.id,
                        'outsider': True
                    }
                    })  
                        
                except Exception as e:
                    # print(e)
                    return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST, 
                            "message": "Failed to register user",
                            "errors": str(e)
                            })   
                            
            else:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to register user",
                        "errors": str(user.error)
                        })         
                
        except Exception as e:
            return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to register user",
                        "errors": str(e)
                        })
            
           
    @csrf_exempt 
    def createPasswordForOutsider(self,request):
        try:

            

            user = User.objects.get( email=request.data['email'] )

            with open('useful.csv') as f:
                reader = csv.reader(f)
                next(reader)      # <- skip the header row
                for row in reader:
                    csv_key = row[0]

            csv_key = csv_key.replace('RUSH','')
            csv_key = csv_key.replace('ISHK','')
            # print(fernet)
            
            user_password = bcrypt.hashpw(request.data['password'].encode('utf-8')  , csv_key.encode('utf-8') ) 
            user.password = user_password
            user.save()
            

            
            response = {
            "success": True,
            "status": status.HTTP_200_OK,                
            "message": "Password changed successfully",
            "data": {
                'user_id' : user.id
            }
            }
            return compress(response)  
        
        except Exception as e:
            response = {
            "success": False,
            "status": status.HTTP_400_BAD_REQUEST,                
            "message": "Incorrect details",
            "errors": str(e)
            }
    
    
    @csrf_exempt
    def addOutsiderDetails(self, request):
        try:
            user_id = request.POST.get("user_id")
            first_name = request.POST.get("firstname")
            last_name = request.POST.get("lastname")
            phone_no = request.POST.get("phone_no")
            gender = request.POST.get("gender")
            dob = request.POST.get("dob")
            department = request.POST.get("department")
            designation = request.POST.get("designation")
            employee_id = request.POST.get("employee_id")
            profile_image = request.FILES.get("profile_image")

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "user_id is required"
                })

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "User not found."
                })

            user.firstname = first_name
            user.lastname = last_name
            user.phone_no = phone_no
            user.save()

            try:
                outsider = OutsiderUser.objects.get(related_id=user.id)
            except OutsiderUser.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Outsider user details not found."
                })

            outsider.gender = gender
            outsider.employee_id = employee_id
            outsider.dob = dob
            outsider.designation=designation
            outsider.department=department
            outsider.processed = 2
            if profile_image:
                outsider.profile_image = profile_image

            outsider.save()
            
            try:
                post_save.disconnect(notification_handler, sender=Notification)
                notification = Notification.objects.create(
                    user_id=user,
                    where_to="user_created",
                    notification_msg=f"Outsider user on boarded with email '{user.email}'. Please review and approve or reject.",
                    action_content_type=ContentType.objects.get_for_model(User),
                    action_id=user.id
                )

                notification.notification_to.set([outsider.added_by, outsider.organization.user_id])
                post_save.connect(notification_handler, sender=Notification)
                post_save.send(sender=Notification, instance=notification, created=True)

            except Exception as e:
                print("Notification creation failed:", e)
            
            

            return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Employee Details added successfully",
                'data': {
                    'employee_user_id': user_id
                }
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            })

    
            
    @csrf_exempt
    def verifyOutsiderUser(self,request):
        try:
            
            user_id = User.objects.get(id = request.data.get('user_id'))
            
            accept =  request.data.get('accept')
            
            outsider_user = OutsiderUser.objects.get(id = request.data.get('outsider_id'))
            
            if accept == "1":
                outsider_user.verified = 1
                outsider_user.processed = 3
                outsider_user.approved_date = timezone.now()
                outsider_user.approved_by=user_id
                outsider_user.save()
                
                
                
                user = User.objects.get(id=outsider_user.related_id.id)
                user.verified = 1
                user.save()
                
            else:
                outsider_user.verified = 2
                outsider_user.approved_date = timezone.now()
                outsider_user.approved_by=user_id
                outsider_user.save()
                
                
                
                user = User.objects.get(id=outsider_user.related_id.id)
                user.verified = 2
                user.save()

            
            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "User Verified successfully"
                    }) 
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Verify User",
                        "errors": str(e)
                        })
            

def thread_to_send_outsider_invitation(email, token):

    sendOutsiderOnBoardLink(email, "https://vibecopilot.ai/?access="+ str(token) + "&os=" + str("true"))