
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.http import QueryDict
from configuration import settings

from digielves_setup.models import TaskAction, TaskChatting, TaskHierarchy, TaskHierarchyAction, TaskHierarchyChatting, Tasks
from asgiref.sync import sync_to_async
from django.core.serializers.json import DjangoJSONEncoder
from itertools import chain
from django.db.models import  F, Value
from django.db.models.functions import Concat
from datetime import datetime
from channels.exceptions import StopConsumer
import logging
import os

logger = logging.getLogger('api_hits')
class TaskChatAndActivityConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        
        query_string = self.scope['query_string'].decode('utf-8')
        query_dict = QueryDict(query_string)
        self.task_id = query_dict.get('task_id')
        self.task_group_name = f"task_{self.task_id}"
        
        # Join task group
        await self.channel_layer.group_add(
            self.task_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Send initial data when connected
        initial_data = await self.get_initial_data()
        await self.send(text_data=json.dumps({
            "success": True,
            "status": 200,
            "message": "Task actions and chats retrieved successfully.",
            "data":initial_data
            
        }))
        
        
    async def cleanup_background_task(self):
        await self.channel_layer.group_discard(
            self.task_group_name,
            self.channel_name
        )

    async def disconnect(self, close_code):
        logger.info("WebSocket disconnected with close code: %s", close_code)
        # Leave task group
        await self.channel_layer.group_discard(
            self.task_group_name,
            self.channel_name
        )
        # Perform cleanup in a background task
        await self.cleanup_background_task()
        

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to task group
        await self.channel_layer.group_send(
            self.task_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # Receive message from task group
    async def chat_message(self, event):
        print("--------------recieved")
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
        
    async def chat_added(self, event):

        await self.send(text_data=json.dumps(event['value']))
    
    async def get_initial_data(self):
        # Use sync_to_async to run synchronous code asynchronously
        try:
            task_chats = await sync_to_async(self.fetch_task_chats)()

            return task_chats
            
        except TaskHierarchy.DoesNotExist:
            return {
                'task_data': None,
                'task_chats': None,
            }
    
    

    def fetch_task_chats(self):
    # Fetch task chats synchronously
        task_actions = TaskHierarchyAction.objects.filter(task_id=self.task_id).select_related('user_id').values(
            'task_id', 'created_at'
        ).annotate(username=Concat('user_id__firstname', Value(' '), 'user_id__lastname'), sender_id=F('user_id'), message=F('remark'))

        task_chats = TaskHierarchyChatting.objects.filter(task_id=self.task_id).values('task_id', 'sender_id', 'message', 'created_at').annotate(username=Concat('sender_id__firstname', Value(' '), 'sender_id__lastname'))

        merged_data = sorted(chain(task_actions, task_chats), key=lambda x: x['created_at'])

        # Convert datetime objects to serializable format
        for item in merged_data:
            item['created_at'] = item['created_at'].strftime('%Y-%m-%dT%H:%M:%S.%fZ') if isinstance(item['created_at'], datetime) else item['created_at']

        
        for item in merged_data:
            if item.get('message') and 'chat_files' in item['message']:
                
                file_path=settings.MEDIA_ROOT+"/"+item.get('message')
                # print(file_path)

                # Get the file size
                try:
                    size = os.path.getsize(file_path)
                    # Convert size to human-readable format
                    size_kb = size / 1024
                    size_str = f"{size_kb:.2f} KB" if size_kb < 1024 else f"{size_kb / 1024:.2f} MB"
                    item['file_size'] = size_str
                except Exception as e:
                    
                    # Handle error if unable to get file size
                    item['file_size'] = 'Unknown'
            else:
                item['file_size'] = -1 
        return merged_data