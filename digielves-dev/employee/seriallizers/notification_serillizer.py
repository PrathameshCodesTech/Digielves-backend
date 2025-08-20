# serializers.py
from rest_framework import serializers
from digielves_setup.models import Notification, Redirect_to




class RedirectToSerializer(serializers.ModelSerializer):
    class Meta:
        model = Redirect_to
        fields = ['link']

class NotificationSerializer(serializers.ModelSerializer):
    redirect_to = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id','notification_msg', 'action_id', 'where_to','other_id','is_seen','created_at','redirect_to']

    def get_redirect_to(self, obj):
        redirect_info = Redirect_to.objects.filter(notification=obj)
        return RedirectToSerializer(redirect_info, many=True).data