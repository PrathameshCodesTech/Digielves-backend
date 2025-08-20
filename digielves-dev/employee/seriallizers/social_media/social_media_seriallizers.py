from digielves_setup.models import SocialMedia
from rest_framework import serializers


class SocialMediadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMedia
        fields = '__all__'