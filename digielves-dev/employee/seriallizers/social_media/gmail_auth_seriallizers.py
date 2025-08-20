from digielves_setup.models import GmailAuth, GmailEmail, MetaAuth
from rest_framework import serializers



class GmailAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = GmailAuth
        fields ="__all__"

class GetGmailAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = GmailAuth
        exclude = ['user_id','platform','id','created_at','updated_at']
        
class GetGmailEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = GmailEmail
        fields = ["email"]
