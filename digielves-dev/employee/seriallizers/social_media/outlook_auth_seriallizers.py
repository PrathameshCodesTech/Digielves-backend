from digielves_setup.models import OutlookAuth
from rest_framework import serializers



class OutlookAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutlookAuth
        fields ="__all__"

class GetOutlookAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutlookAuth
        fields ="__all__"       