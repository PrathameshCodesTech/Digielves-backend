import asyncio
import decimal
import json
from datetime import datetime
from telethon.sync import TelegramClient
from telethon.tl.types import PeerChannel
from telethon.tl.functions.messages import GetHistoryRequest

async def get_messages(api_id, api_hash, mobile_number, session_path):

    try:
        # Creating a telegram session and assigning it to a variable client
        client = TelegramClient(session_path, api_id, api_hash)
        await client.start()

        if mobile_number.isdigit():
            numeric_mobile_number = "+91 " + mobile_number
            entity = numeric_mobile_number

            # entity = PeerChannel(decimal(numeric_mobile_number))
        else:
            entity = mobile_number

        my_channel = await client.get_entity(entity)

        offset_id = 0
        limit = 100
        all_messages = []
        total_messages = 0
        total_count_limit = 0
        messages_data = [] 

        while True:
            print("Current Offset ID is:", offset_id, "; Total Messages:", total_messages)
            history = await client(GetHistoryRequest(
                peer=my_channel,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            ))
            # if not history.messages:
            #     break
            messages = history.messages
            

            if messages:
            

                for message in messages:
                    message_data = {
                        "message": message.message, 
                        "out": message.out,
                        "date": message.date,
                    }
                    messages_data.append(message_data)
                offset_id = messages[-1].id 
                messages_data = sorted(messages_data, key=lambda x: x["date"])
            
                return messages_data 
            else:
                
                return []
        

    except Exception as e:
        print(f"Error during Telegram message retrieval: {str(e)}")
        return False

    finally:
        await client.disconnect()

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, bytes):
            return list(o)

        return json.JSONEncoder.default(self, o)

# You can call the get_messages function from another script or a separate module
