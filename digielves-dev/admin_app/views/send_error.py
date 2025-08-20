
from django.http import JsonResponse


from digielves_setup.send_emails.email_conf.send_error_email import SendError
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt

    
class SendErrorViewSet(viewsets.ModelViewSet):
    
    @csrf_exempt
    def sendError(self,request):
        user_id = request.POST.get('user_id')
        error = request.POST.get('error')
        print()
        email = "send.error.me@gmail.com"
        SendError(email,error)
        return JsonResponse("success",safe=False)