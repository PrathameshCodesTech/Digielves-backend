from digielves_setup.models import MetaAuth
from rest_framework import serializers


class MetaAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaAuth
        exclude = ['profile_picture']


class GetMetaAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaAuth
        fields ="__all__"


class PutMetaAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaAuth
        exclude = ['profile_picture','metaplatform_id']