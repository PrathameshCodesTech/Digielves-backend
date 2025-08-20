import json
from django.http import QueryDict
from channels.generic.websocket import AsyncWebsocketConsumer

class ProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode('utf-8')
        query_dict = QueryDict(query_string)
        self.user_id = query_dict.get('user_id')
        self.progress_group_name = f"progress_{self.user_id}"

        await self.channel_layer.group_add(
            self.progress_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.progress_group_name,
            self.channel_name
        )

    async def send_progress(self, event):
        message = event['message']
        print("🐍 File: digielves_setup/progress_consumer.py | Line: 27 | ProgressConsumer ~ message",message)
        await self.send(text_data=json.dumps(message))

class ProgressConsumerForTaskProject(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode('utf-8')
        query_dict = QueryDict(query_string)
        self.user_id = query_dict.get('user_id')
        self.progress_group_name = f"task_progress_{self.user_id}"

        await self.channel_layer.group_add(
            self.progress_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.progress_group_name,
            self.channel_name
        )

    async def send_task_progress(self, event):
        message = event['message']
        print("🐍 File: digielves_setup/progress_consumer.py | Line: 27 | ProgressConsumer ~ message",message)
        await self.send(text_data=json.dumps(message))

        
