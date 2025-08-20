

from telethon.sync import TelegramClient
import os
async def handle_telegram_msg(api_id, api_hash, mobile_number, session,msg):
    try:
        if not os.path.isfile(session):
            print("Session file does not exist.")
            return False
        client = TelegramClient(session, api_id, api_hash)

        async def send_message():
            await client.start()
            if mobile_number.isdigit():
                
                await client.send_message(f"+91 {mobile_number}", msg)
            else:
                
                await client.send_message(mobile_number, msg)
            await client.disconnect()

        await send_message()

        return True

    except Exception as e:
        print(f"Error during Telegram login: {str(e)}")
        return False
    
    # if not os.path.exists(session_file):
    #     return "Not logged in. Session file not found."

    # try:
    #     async with TelegramClient(session_path, api_id, api_hash) as client:
    #         await client.send_message(username, message)
    #     return "Message sent successfully."
    # except Exception as e:
    #     return f"Error sending message: {str(e)}"
