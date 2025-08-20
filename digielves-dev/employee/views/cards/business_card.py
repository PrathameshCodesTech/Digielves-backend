import random
from django.http import JsonResponse
from digielves_setup.models import BgImage, BusinessCard, User
from digielves_setup.send_emails.email_conf.send_business_card import sendBusinessCard
from employee.seriallizers.bg_image_seriallizers import BgImageSerializer

from employee.seriallizers.cards.business_card_serillizers import BusinessCardSerializer, GetAllBusinessCardSerializer
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status



class BusinessCardViewSet(viewsets.ModelViewSet):
    
    @csrf_exempt
    def add_business_card(self,request):
        try:
            user_id = request.data.get('user_id')
            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. 'user_id' is required."
                }, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(id=user_id)
            serializer = BusinessCardSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user_id=user_id)
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Business card created successfully.",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create business card.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found."
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return JsonResponse({
                "JsonResponse": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"An error occurred: {str(e)}",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    @csrf_exempt
    def get_business_cards(self,request):
        user_id = request.GET.get('user_id')
        card_id = request.GET.get('card_id')
        try:
            if card_id:
                business_card = BusinessCard.objects.get(id=card_id, user_id=user_id)
                serializer = BusinessCardSerializer(business_card)
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Business card retrieved successfully.",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            else:
                business_cards = BusinessCard.objects.filter(user_id=user_id)
                serializer = GetAllBusinessCardSerializer(business_cards, many=True)
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Business cards retrieved successfully.",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)

        except BusinessCard.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Business card not found."
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"An error occurred: {str(e)}",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    @csrf_exempt
    def update_business_card(self,request):
        user_id = request.data.get('user_id')
        card_id = request.data.get('card_id')
        try:
            business_card = BusinessCard.objects.get(id=card_id,user=user_id)
            serializer = BusinessCardSerializer(business_card, data=request.data)
            
            if serializer.is_valid():
                # Delete previous image if a new image is sent by the user
                if 'card_image' in request.data:
                    business_card.card_image.delete()
                if 'profile_image' in request.data:
                    business_card.card_image.delete()
                        
                
                serializer.save()
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Business card updated successfully.",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to update business card.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except BusinessCard.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Business card not found."
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"An error occurred: {str(e)}",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @csrf_exempt
    def delete_business_card(self,request):
        user_id = request.GET.get('user_id')
        card_id = request.GET.get('card_id')
        try:
            business_card = BusinessCard.objects.get(id=card_id)
            business_card.delete()
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Business card deleted successfully."
            }, status=status.HTTP_200_OK)

        except BusinessCard.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Business card not found."
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"An error occurred: {str(e)}",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    
    @csrf_exempt
    def send_business_card(self, request):
        


        card = request.FILES.get('business_card')
        user_id = request.data.get('user_id')
        
        emails_str = request.data.get('emails', '')
        email_ids = [str(email) for email in emails_str.split(',') if email.strip()]
        print(type(card))
        user_id = User.objects.get(id=user_id)
        try:
            for email in email_ids:

                sendBusinessCard(email,card,f"{user_id.firstname} {user_id.lastname}")
                pass
        except Exception as e:
            response_data = {
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred while sending the card.",
                "errors": str(e)
            }
            return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        response_data = {
            "success": True,
            "status": status.HTTP_201_CREATED,
            "message": "Card Sent successfully"
            
        }
        return JsonResponse(response_data, status=status.HTTP_201_CREATED)