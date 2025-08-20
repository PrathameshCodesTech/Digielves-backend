from digielves_setup.models import SalesAttachments
from rest_framework import serializers


class SalesAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesAttachments
        fields = ['id','sales_lead','attachment']

