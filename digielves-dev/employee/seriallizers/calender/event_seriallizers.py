from rest_framework import serializers

from digielves_setup.models import Events

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        exclude = ['guest','attachment']

class EventSerializers(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = '__all__'
