
from asyncio import Event
from django.http import JsonResponse

from configuration.gzipCompression import compress
from digielves_setup.models import EmployeePersonalDetails, User, Birthdays
from digielves_setup.send_emails.email_conf.send_bd_wish import sendBdWishLink
from employee.seriallizers.calender.birthday_seriallizers import EmployeePersonalDetailsforBirthdaySerializer, BirthdaysSerializer,AddBirthdaysSerializer
from employee.seriallizers.personal_details_seriallizer import EmployeePersonalDetailsSerializer

from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from datetime import datetime
from django.utils import timezone

class BirthdayViewset(viewsets.ModelViewSet):


    serializer_class = EmployeePersonalDetailsSerializer

    @csrf_exempt    
    def getBirthday(self, request):
        try:
            user_id = request.GET.get('user_id')
            today_only = request.GET.get('restrict_to_today_birthdays', 'false').lower() == 'true' or request.GET.get('restrict_to_today_birthdays', 'false').lower() == True
            
    
            # user = User.objects.get(id=user_id)
    
            employee_details = EmployeePersonalDetails.objects.get(user_id=user_id)
            
            employees = EmployeePersonalDetails.objects.filter(organization_id=employee_details.organization_id,organization_location=employee_details.organization_location)
            if today_only:
                today = datetime.now().date()
                employees = employees.filter(date_of_birth__contains=today.strftime("%m-%d"))

            birthdays = Birthdays.objects.filter(user_id=user_id)
            if today_only:
                birthdays = birthdays.filter(date_of_birth__contains=today.strftime("%m-%d"))
            employee_serializer = EmployeePersonalDetailsforBirthdaySerializer(employees, many=True)
            birthdays_serializer = BirthdaysSerializer(birthdays, many=True)
    
            combined_data =  birthdays_serializer.data + employee_serializer.data
    
            response = {
                "success": True,
                "status": 200,
                "message": "Birthday retrieved successfully",
                "data": combined_data
            }
    
            return JsonResponse(response, safe=False)
        except User.DoesNotExist:
            response = {
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "error": 'User not found'
            }
            return JsonResponse(response)
        except Exception as e:
            response = {
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": 'An error occurred while processing the request.'
            }
            return JsonResponse(response)

            
            

    @csrf_exempt
    def add_birthday(self, request):
        try:
            # Attempt to create a new Birthday instance
            birthday = Birthdays.objects.create(
                user_id=User.objects.get(id=request.POST.get('user_id')),
                firstname=request.POST.get('firstname'),
                lastname=request.POST.get('lastname'),  
                date_of_birth=request.POST.get('date_of_birth'),
                email=request.POST.get('email'),
                profile_picture=request.FILES.get('profile_picture'),
                phone_no=request.POST.get('phone_no'), 
            )

            response_data = {
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Birthday Added successfully",
                "data": AddBirthdaysSerializer(birthday).data  # Serialize the created instance
            }
            return JsonResponse(response_data, status=status.HTTP_201_CREATED)

        except User.DoesNotExist:
            response_data = {
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found."
            }
            return JsonResponse(response_data, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            response_data = {
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred while adding birthday.",
                "error": str(e)
            }
            return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   

        
    @csrf_exempt
    def get_birthdays(self,request):
        print("---------")
        user_id = request.GET.get('user_id')
    
        if not user_id:
            response = {
                "success": False,
                "status": 400,
                "error": 'Please provide a user_id in the request query params.'
            }
            return JsonResponse(response)
    
        try:
            birthdays = Birthdays.objects.filter(user_id=user_id)
            serializer = BirthdaysSerializer(birthdays, many=True)
            response = {
                "success": True,
                "status": 200,
                "message": "Birthday retrieved successfully",
                "data": serializer.data
            }
            return JsonResponse(response)
        except Birthdays.DoesNotExist:
            return JsonResponse({
            "success": True,
            'message': 'No birthdays found for the given user_id.'}, status=404)
            
        
    def update_birthday(self,request):
        try:
            birthday_id = request.data.get('birthday_id')
            user_id = request.data.get('user_id')
            birthday = Birthdays.objects.get(id=birthday_id)
        except Birthdays.DoesNotExist:
            return JsonResponse({'message': 'Birthday not found'}, status=404)
    
        serializer = BirthdaysSerializer(birthday, data=request.data, partial=True)
    
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({"success": True,'message': 'Birthday updated successfully'})
        return JsonResponse(serializer.errors, status=400)


    def Birthdaydelete(self, request):
        user_id = request.GET.get('user_id')
        birthday_id = request.GET.get('birthday_id')

        if birthday_id is None:
            return JsonResponse({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            birthdays = Birthdays.objects.filter(id=birthday_id)
            if birthdays.exists():
                birthdays.delete()
                return JsonResponse({"success": True,"message": "Birthdays deleted successfully"})
            else:
                return JsonResponse({"error": "No Birthdays records found for the specified user_id"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





    
    @csrf_exempt
    def send_bd_wish(self, request):
        


            card = request.FILES.get('bd_card')
            user_id = request.data.get('user_id')
            birthday_id = request.data.get('birthday_id')
            
            print(card)
            
            user_name = User.objects.get(id=user_id)
            try:
                bd_card = Birthdays.objects.get(id = birthday_id,user_id=user_id)
                bd_card.bdCard=card
                bd_card.save()
                
                sendBdWishLink(bd_card.email,card,f"{user_name.firstname} {user_name.lastname}")
            except Exception as e:
                response_data = {
                    "success": False,
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "An error occurred while saving the card.",
                    "errors": str(e)
                }
                return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            response_data = {
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Card Added successfully"
                
            }
            return JsonResponse(response_data, status=status.HTTP_201_CREATED)



