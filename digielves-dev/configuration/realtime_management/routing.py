# routing.py

from django.urls import re_path

from digielves_setup.consumers import NotificationConsumer
websocket_urlpatterns = [
    re_path(r'ws/notifications/(?P<user_id>\d+)/$', NotificationConsumer.as_asgi()),
]
