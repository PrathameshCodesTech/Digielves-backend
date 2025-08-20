from rest_framework import serializers
from digielves_setup.models import Address





class UserAddressSerializers(serializers.ModelSerializer):
    class Meta:
        model=Address
        fields = '__all__'

class UpdateUserAddressSerializers(serializers.ModelSerializer):
    class Meta:
        model=Address
        fields = fields = ['user_id', 'street_name','land_mark','city','pincode','state','country','Organization_code','description','created_at','updated_at']      
