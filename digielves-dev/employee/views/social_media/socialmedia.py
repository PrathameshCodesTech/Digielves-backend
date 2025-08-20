

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from digielves_setup.models import GmailAuth, MetaAuth, SocialMedia, TelegramAuth, OutlookAuth
from employee.seriallizers.social_media.social_media_seriallizers import SocialMediadSerializer

from rest_framework import status
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Max
from decimal import Decimal
import math
class SocialMediaViewSet(viewsets.ModelViewSet):

    serializer_class = SocialMediadSerializer
    
    

    @csrf_exempt
    def AddSocialmedia(self, request):
        user_id = request.data.get('user_id')
        platform = request.data.get('platform')
        
        # Find all matching objects based on user_id and platform
        social_media_data = SocialMedia.objects.filter(user_id=user_id, platform=platform)
        
        if social_media_data.exists():
            # Update all matching objects to set active to True
            social_media_data.update(active=True)
            
            # Serialize and return the updated objects
            serializer = SocialMediadSerializer(social_media_data, many=True)
            
            response_data = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Data updated successfully.",
                "data": serializer.data
            }
            return JsonResponse(response_data)
        else:
            # No matching record exists, so create a new one
            serializer = SocialMediadSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                response_data = {
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Data created successfully.",
                    "data": serializer.data
                }
                return JsonResponse(response_data, status=status.HTTP_201_CREATED)
            else:
                response_data = {
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create or update data.",
                    "errors": serializer.errors
                }
                return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)


        

    @csrf_exempt
    def get_social_media_by_user(self,request):
        try:
            user_id = request.GET.get('user_id')
            
            social_media_data = SocialMedia.objects.filter(user_id=user_id, active=True)

            data = [{'platform': item.platform, 'active': item.active} for item in social_media_data]
            response_data = {
            "success": True,
            "status": 200,
            "message": "Data retrieved successfully",
            "data": data
        }
        
            
            return JsonResponse(response_data)
        except SocialMedia.DoesNotExist:
            return JsonResponse({'message': 'User not found'}, status=404)
        
    @csrf_exempt
    def UpdateSocialMedia(self,request):
        user_id = request.data.get('user_id')
        platform = request.data.get('platform')
        active = request.data.get('active', False) 
        
        try:
            social_media = SocialMedia.objects.get(user_id=user_id, platform=platform)
            print(social_media.active)
            
            if social_media.active != active:
                social_media.active = active
                social_media.save()
                
                serializer = SocialMediadSerializer(social_media)
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Social media data updated successfully.",
                    "data": serializer.data
                })
            else:
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Social media data is already in the requested state."
                })
        
        except SocialMedia.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Social media data not found for the provided user_id and platform."
            }, status=status.HTTP_404_NOT_FOUND)
        



class SocialMediaAuthViewSet(viewsets.ModelViewSet):

    serializer_class = SocialMediadSerializer

    def get_auth_info(self, request):
        print("--------------------------")
        try:
            user_id = request.GET.get('user_id')
            print(user_id)
        
            try:
                #meta_auth = MetaAuth.objects.get(user_id=user_id)
                
                meta_auth_records = MetaAuth.objects.filter(user_id=user_id)

                instagram={}
                facebook={}
                
                if meta_auth_records:
                
                    for meta_auth in meta_auth_records:
                        if meta_auth.metaplatform == "Facebook":
                            facebook = {
                            'platform': meta_auth.metaplatform if meta_auth else 'Facebook',
                            'status_login': meta_auth.status_login if meta_auth else False,
                            }
                            instagram={
                            'platform': 'Instagram',
                            'status_login': False,
                            }
                        if meta_auth.metaplatform == "Instagram":
                            instagram = {
                            'platform': meta_auth.metaplatform if meta_auth else 'Instagram',
                            'status_login': meta_auth.status_login if meta_auth else False,
                            }
                            facebook={
                            'platform': 'Facebook',
                            'status_login': False,
                            }
                else:
                    facebook={
                            'platform': 'Facebook',
                            'status_login': False,
                            }
                    instagram={
                            'platform': 'Instagram',
                            'status_login': False,
                            }
                        
            except MetaAuth.DoesNotExist:
                meta_auth = None
            
            try:
                gmail_auth = GmailAuth.objects.get(user_id=user_id)
            except GmailAuth.DoesNotExist:
                gmail_auth = None
        
            try:
                tele_auth_queryset = TelegramAuth.objects.filter(user_id=user_id)
                tele_auth_instance = tele_auth_queryset.first()
            except TelegramAuth.DoesNotExist:
                tele_auth_instance = None
            
            try:
                outlook_auth_queryset = OutlookAuth.objects.filter(user_id=user_id)
                outlook_auth_instance = outlook_auth_queryset.first()
            except OutlookAuth.DoesNotExist:
                outlook_auth_instance = None
        
#            meta_auth_data = {
#                'platform': meta_auth.metaplatform if meta_auth else 'Facebook',
#                'status_login': meta_auth.status_login if meta_auth else False,
#            }
            
            gmail_auth_data = {
                'platform': 'Gmail',
                'status_login': gmail_auth.status_login if gmail_auth else False,
            }
        
            tele_auth_data = {
                'platform': tele_auth_instance.platform if tele_auth_instance else 'Telegram',
                'status_login': tele_auth_instance.status_login if tele_auth_instance else False,
            }
            
            outlook_auth_data = {
                'platform': outlook_auth_instance.platform if outlook_auth_instance else 'Outlook',
                'status_login': outlook_auth_instance.status_login if outlook_auth_instance else False,
            }
        
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Social media data updated successfully.",
                "data": [instagram,facebook, gmail_auth_data, tele_auth_data, outlook_auth_data]
            })
        except Exception as e: 
            
            return JsonResponse({
                      "success": False,
                      "status": 500,
                      "message": e
                  })
        
