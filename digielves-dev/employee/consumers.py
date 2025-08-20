from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json
class TestConsumer(WebsocketConsumer):
    
    def connect(self):
        # Called on connection.
        # To accept the connection call:
        self.room_name = "test_consumer"
        self.room_group_name = "test_consumer_group"
        async_to_sync(self.channel_layer.group_add)(
            self.room_name,self.room_group_name
        )
        self.accept()
        self.send(text_data=json.dumps({"status": "Connected"}))
        # self.close()

    def receive(self):
        pass

    def disconnect(self):
        pass