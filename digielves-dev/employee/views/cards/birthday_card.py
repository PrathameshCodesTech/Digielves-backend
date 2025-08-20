from django.http import JsonResponse

from configuration.gzipCompression import compress
from digielves_setup.models import  BirthdayTemplates, Birthdays, EmployeePersonalDetails, User

from employee.seriallizers.cards.birthday_card_seriallizers import  GetBdTemplateCardSerializer, GetBdWithTempCardSerializer, GetUniqueBdTemplateCardSerializer, GetUserDetailsSerializer
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
class BirthdayViewSet(viewsets.ModelViewSet):
    # serializer_class = HelpdeskCreateSerializer

    

    @csrf_exempt
    def add_bd_card(self, request):
        try:
            user_id = request.data.get('user_id')
            bd_id = request.data.get('bd_id')
            card = request.FILES.get('card') 
            bd_wish =  request.data.get('bd_wish')
            card_name =  request.data.get('card_name')
            card_profile = request.FILES.get('card_profile') 
            

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. 'user_id' is required."
                }, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(id=user_id)
            bd = Birthdays.objects.get(id=bd_id)
            BirthdayTemplates.objects.create(
                user_id = user,
                birthday = bd,
                card_name = card_name,
                bdCard = card,
                bd_wish = bd_wish,
                card_profile = card_profile
            )
            
            bd.card_added = True
            
            bd.save()

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Birthday card added successfully."
            })

        except ObjectDoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Birthday or user not found."
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @csrf_exempt
    def get_bd_templates(self, request):
        try:
            user_id = request.GET.get('user_id')
            temp_id = request.GET.get('template_id')
            bd_id = request.GET.get('bd_id')

            if temp_id:
                
                temp_data = BirthdayTemplates.objects.filter(
                    user_id=user_id,
                    id = temp_id    
                )
                serialized_data = GetUniqueBdTemplateCardSerializer(temp_data, many=True)
                
            elif bd_id:
                bd_temp = BirthdayTemplates.objects.filter(
                    user_id=user_id,
                    birthday = bd_id    
                )
                serialized_data = GetBdWithTempCardSerializer(bd_temp, many=True)
            else:
                temp_data = BirthdayTemplates.objects.filter(
                    user_id=user_id)

                serialized_data = GetBdTemplateCardSerializer(temp_data, many=True)
            
            

            return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Profile Getting successfully",
                'data': serialized_data.data
            })

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=404)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to Get Profile Details",
                "errors": str(e)
            })

                
    @csrf_exempt
    def get_user_details(self,request):
        try:
            user_id = request.GET.get('user_id')


            
            employe_data = EmployeePersonalDetails.objects.filter(user_id=user_id)
            seriallized_data = GetUserDetailsSerializer(employe_data, many=True)
        
            return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,                
                "message": "Profile Getting successfully",
                'data': seriallized_data.data
                })
  
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=404)
        
        
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to Get Profile Details",
                        "errors": str(e)
                        })