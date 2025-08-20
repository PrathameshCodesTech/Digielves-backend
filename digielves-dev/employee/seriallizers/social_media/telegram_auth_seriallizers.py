from digielves_setup.models import TeleUser, TelegramAuth
from rest_framework import serializers


class TelegramAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramAuth
        fields = ['user_id', 'mobile_number', 'username', 'otp', 'other_field', 'session_file','password']

class TeleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeleUser
        fields ="__all__"