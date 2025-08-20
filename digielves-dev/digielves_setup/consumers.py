from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async
import json
from django.http import QueryDict
from configuration import settings
from digielves_setup.models import Notification
from channels.exceptions import StopConsumer
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger('api_hits')

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract user_id from URL parameters
        query_string = self.scope['query_string'].decode('utf-8')
        query_dict = QueryDict(query_string)
        self.user_id = query_dict.get('user_id')

        if not self.user_id:
            await self.close()
            return

        self.user_channel_name = f"user_{self.user_id}"
        await self.channel_layer.group_add(
            self.user_channel_name,
            self.channel_name
        )

        # Send initial data when connected
        notifications = await self.fetch_notifications()
        serialized_notifications = self.serialize_notifications(notifications)
        await self.accept()

        await self.send_notification_message(serialized_notifications)

    async def cleanup_background_task(self):
        await self.channel_layer.group_discard(
            self.user_channel_name,
            self.channel_name
        )

    async def disconnect(self, close_code):
        logger.info("WebSocket disconnected with close code Noti: %s", close_code)
        await self.channel_layer.group_discard(
            self.user_channel_name,
            self.channel_name
        )
        await self.cleanup_background_task()

    async def receive(self, text_data):
        # Handle receiving messages (if needed)
        pass

    async def send_notification_message(self, data):
        await self.send(text_data=json.dumps({
            'success': True,
            'status': 200,
            'data': data,
        }))

    async def notification_added(self, event):
        await self.send(text_data=json.dumps(event['value']))

    async def notification_message(self, event):
        # Send notification to WebSocket
        await self.send(text_data=json.dumps(event))

    def serialize_notifications(self, notifications):
        # Serialize Notification objects to a format suitable for sending over WebSocket
        serialized_notifications = []

        for notification in notifications:
            
            serialized_notification = {
                'id': notification.id,
                'notification_msg': notification.notification_msg,
                'created_at': str(notification.created_at),
                'is_seen': notification.is_seen,
                'where_to': notification.where_to,
                'other_id': notification.other_id,
                'action_id': notification.action_id,
                'is_clicked':notification.is_clicked
            }
            serialized_notifications.append(serialized_notification)
        return serialized_notifications

    @database_sync_to_async
    def fetch_notifications(self):
        return list(Notification.objects.filter(notification_to=self.user_id).order_by("-created_at"))