from rest_framework import serializers

from digielves_setup.models import SummeryNdTask





class SummeryNdTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummeryNdTask
        fields = '__all__'