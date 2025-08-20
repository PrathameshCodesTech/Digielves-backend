

from digielves_setup.models import SalesStatus
from rest_framework import serializers


class SalesStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesStatus
        fields = [
            'id', 'status_name', 'fixed_state',
            'color', 'order','created_at'
        ]