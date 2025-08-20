# serializers.py

from digielves_setup.models import BusinessCard
from rest_framework import serializers
from datetime import datetime

class BusinessCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessCard
        fields = '__all__'

class GetAllBusinessCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessCard
        fields = ['id','card_name','card_image']

