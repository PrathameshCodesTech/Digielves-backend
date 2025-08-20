

# Django Required Dependencies
from django.shortcuts import render
from rest_framework import viewsets
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status


# Authentication Modules for rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.permissions import  IsAuthenticated ,AllowAny

from django.db.models import Max


# Application Response Serializer 



from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from configuration.authentication import JWTAuthenticationUser
from digielves_setup.models import Address
from digielves_setup.seriallizers.address import UserAddressSerializers,UpdateUserAddressSerializers

class UserAddressClass(viewsets.ModelViewSet):

    authentication_classes = [JWTAuthenticationUser]
    #permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]

    throttle_classes = [AnonRateThrottle,UserRateThrottle]
    serializer_class =UserAddressSerializers



    
    # permission_classes = [AllowAny]
        
        
    # Client Registration API 
    @csrf_exempt
    def addUserAddress(self,request):
        userAddress=Address()
        try:
            userAddressSerialData = UserAddressSerializers(userAddress,data=request.data)
            try:
                print("byeee")
                if userAddressSerialData.is_valid(raise_exception=True):
                        userAddressSerialData.save()

                        return JsonResponse({
                        "success": True,
                        "status": status.HTTP_201_CREATED,                
                        "message": "user Address created successfully",
                        "data": {
                                'address_id' : userAddress.id
                }
                        })        
            except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to create user address",
                        "errors": str(e)
                        })
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to create user address",
                        "errors": str(e)
                        })
                
    # Client Registration API 
    @csrf_exempt
    def updateUserAddress(self,request):
        userAddress=Address.objects.get(id= request.data['address_id'] )
        try:
            userAddressSerialData = UpdateUserAddressSerializers(userAddress,data=request.data)
            try:
                print("byeee")
                if userAddressSerialData.is_valid(raise_exception=True):
                        userAddressSerialData.save()

                        return JsonResponse({
                        "success": True,
                        "status": status.HTTP_201_CREATED,                
                        "message": "user Address updated successfully",
                        "data": {
                                'address_id' : userAddress.id
                }
                        })        
            except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to update user address",
                        "errors": str(e)
                        })
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to update user address",
                        "errors": str(e)
                        })
                                
