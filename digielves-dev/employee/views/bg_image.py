import random
from django.http import JsonResponse
from digielves_setup.models import BgImage, User
from employee.seriallizers.bg_image_seriallizers import BgImageSerializer

from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status



class BgImageViewSet(viewsets.ModelViewSet):
    

    def check_bg_image(self, user_id):
        try:
            return BgImage.objects.get(user_id=user_id)
        except BgImage.DoesNotExist:
            return None

    @csrf_exempt
    def add_bg_image(self, request):
        
        try:
            print("-----------")
            user_id = request.data.get('user_id')
            image = request.data.get('image')
            index = request.data.get('index')
            
            print(image)

            if not user_id or not image:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. 'user_id' and 'image' are required fields."
                })

            user = User.objects.get(id=user_id)
            bg_image = self.check_bg_image(user_id)

            if bg_image:
                try:
                    bg_image.image.delete(save=False)
                except:
                    pass
                bg_image.image = image
                bg_image.index = index
            else:
                bg_image = BgImage(user=user, image=image, index=index)

            bg_image.save()

            serializer = BgImageSerializer(bg_image)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "BgImage created or updated successfully.",
                "data": serializer.data
            })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found."
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"An error occurred: {str(e)}",
            })
            
    @csrf_exempt
    def get_bg_image(self, request):       
        try:
            user_id = request.GET.get('user_id')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. 'user_id' is a required parameter."
                })

            user = User.objects.get(id=user_id)
            bg_image = BgImage.objects.filter(user=user).first()

            if not bg_image:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "BgImage not found for the specified user."
                })

            
            serializer = BgImageSerializer(bg_image)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "BgImage retrieved successfully.",
                "data": serializer.data
            })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found."
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"An error occurred: {str(e)}",
            })