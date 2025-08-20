
from rest_framework import viewsets
from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt

from digielves_setup.models import Notification, Redirect_to, User
from employee.seriallizers.notification_serillizer import NotificationSerializer
from rest_framework import status

class NotificationClass(viewsets.ModelViewSet):

    @csrf_exempt
    def get_notifications(self,request):
        user_id = request.GET.get('user_id')
    
        if not user_id:
            return JsonResponse({"error": "user_id parameter is required"}, status=400)
            
    
        try:
            notifications = Notification.objects.filter(notification_to=user_id).order_by("-created_at")
            serializer = NotificationSerializer(notifications, many=True)
    
            

                    
            return JsonResponse({
                    "success": True,
                    "status": 200,                 
                    'data':serializer.data,
                    
                        
                    }) 
    
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            
    
    @csrf_exempt
    def update_notifications(self,request):
        try:
            user_id = request.POST.get('user_id')
            notification_id = request.POST.get('notification_id')
        
            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id is missing."
                }, status=status.HTTP_400_BAD_REQUEST)
        
            try:
                if not notification_id:
                    notifications = Notification.objects.filter(notification_to=user_id, is_seen=False)
                
                    if notifications.exists():
                        notifications.update(is_seen=True)
                        return JsonResponse({
                            "success": True,
                            "status": status.HTTP_200_OK,
                            "message": f"Notifications Updated",
                        }, status=status.HTTP_200_OK)
                    else:
                        return JsonResponse({
                            "success": True,
                            "status": status.HTTP_200_OK,
                            "message": "No unseen notifications to update.",
                        }, status=status.HTTP_200_OK)
                else:
                    print(notification_id)
    
                    notification = Notification.objects.get(notification_to=user_id, id=notification_id, is_seen=False)
                    print(notification)
                    if notification:
                        notification.is_seen = True
                        notification.save()
                        return JsonResponse({
                            "success": True,
                            "status": status.HTTP_200_OK,
                            "message": f"Notification {notification_id} Updated",
                        }, status=status.HTTP_200_OK)
        
            except Notification.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Notification not found.",
                }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
        
    @csrf_exempt
    def mark_notifications_as_clicked(self,request):
        try:
            user_id = request.POST.get('user_id')
        
            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id is missing."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if the user exists
            if not User.objects.filter(id=user_id).exists():
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "User not found.",
                }, status=status.HTTP_404_NOT_FOUND)

            # Update notifications for the user
            notifications = Notification.objects.filter(notification_to=user_id,is_clicked=False)
            count = notifications.update(is_clicked=True)

            if count > 0:
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": f"{count} notifications marked as clicked.",
                }, status=status.HTTP_200_OK)
            else:
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "No unseen notifications to mark as clicked.",
                }, status=status.HTTP_200_OK)
        
        except Exception as e:
            # Log the exception for debugging purposes
            # logger.error("Error marking notifications as clicked: %s", str(e))
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to mark notifications as clicked. Please try again later.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
