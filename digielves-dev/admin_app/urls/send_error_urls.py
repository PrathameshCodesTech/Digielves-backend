
from django.urls import path

from admin_app.views.send_error import SendErrorViewSet








urlpatterns = [

    path(r'send_mail/',SendErrorViewSet.as_view({'post':'sendError'})),
    

] 