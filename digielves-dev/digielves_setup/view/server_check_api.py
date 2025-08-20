

from rest_framework import viewsets
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status

from rest_framework.permissions import  AllowAny


class CheckClass(viewsets.ModelViewSet):

    permission_classes = [AllowAny]
    @csrf_exempt
    def check_server(self,request):
        
        data = {"success": True}
        
        return JsonResponse(data)