from digielves_setup.models import Policies
from rest_framework import serializers


class GetPolicyRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Policies
        fields = '__all__'
        

class GetSpecificPolicyRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Policies
        fields = '__all__'