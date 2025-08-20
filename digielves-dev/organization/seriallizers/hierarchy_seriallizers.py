
from digielves_setup.models import User, UserCreation
from rest_framework import serializers


class HierarchyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']
        

class HierarchyUserCreationSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserCreation
        fields = ['id', 'email']
