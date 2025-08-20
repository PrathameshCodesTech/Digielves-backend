from django.http import JsonResponse
from digielves_setup.models import BgImage, BusinessCard, User, UserFilters
from employee.seriallizers.bg_image_seriallizers import BgImageSerializer

from employee.seriallizers.cards.business_card_serillizers import BusinessCardSerializer, GetAllBusinessCardSerializer
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from django.shortcuts import get_object_or_404
# from django.utils.translation import ugettext_lazy as _

class BoardViewFilterViewSet(viewsets.ModelViewSet):
    
    
    # api for both POST and PUT
    @csrf_exempt
    def add_board_view_filter(self,request):
        try:
            user_id = request.data.get('user_id')
            board_view = request.data.get('board_view')
            board_name = request.data.get('board_name')

            if not user_id or not board_view:
                return JsonResponse({
                    "success": False,
                    "message": _("Both user_id and board_view are required.")
                }, status=status.HTTP_400_BAD_REQUEST)

            user = get_object_or_404(User, id=user_id)

            defaults = {}
            if board_name == "custom_board":
                defaults['custom_board_view'] = board_view
            elif board_name == "myboard":
                defaults['myboard_view'] = board_view
            elif board_name == "personal_board":
                defaults['personal_board_view'] = board_view
            elif board_name == "sales_board":
                defaults['sales_board_view'] = board_view

            user_filter, created = UserFilters.objects.update_or_create(user=user, defaults=defaults)



            return JsonResponse({
                "success": True,
                # "message": message,
                # "data": UserFiltersSerializer(user_filter).data
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": _("User not found.")
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": _("An error occurred: {}").format(str(e))
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)