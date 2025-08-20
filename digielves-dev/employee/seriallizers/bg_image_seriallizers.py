# serializers.py

from digielves_setup.models import BgImage
from rest_framework import serializers
from datetime import datetime

class BgImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    class Meta:
        model = BgImage
        fields = ['image','index']
        
    def get_image(self, obj):
        # Assuming obj.image.url is the image URL, modify it to include datetime
        image_url = f"{obj.image.url}/?datetime={datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}"
        return image_url
