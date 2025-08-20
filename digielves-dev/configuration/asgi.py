import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configuration.settings')
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path

from digielves_setup.async_consumer import TaskChatAndActivityConsumer
from digielves_setup.consumers import NotificationConsumer
from digielves_setup.progress_consumer import ProgressConsumer, ProgressConsumerForTaskProject

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configuration.settings')

django_asgi_application = get_asgi_application()

ws_patterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()), 
    path("ws/get_chats_and_activities/", TaskChatAndActivityConsumer.as_asgi()),
    path("ws/sales_lead/progress/", ProgressConsumer.as_asgi()),
    path("ws/task_project/progress/", ProgressConsumerForTaskProject.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": django_asgi_application,
    "websocket": AuthMiddlewareStack(URLRouter(ws_patterns)),
})
