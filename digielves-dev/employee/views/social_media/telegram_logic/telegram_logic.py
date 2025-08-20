import asyncio
from digielves_setup.models import TelegramAuth
from telethon.sync import TelegramClient
from django.conf import settings
from asgiref.sync import sync_to_async

async def handle_telegram_login(user_id,api_id, api_hash, mobile_number):
    
    user_folder = settings.MEDIA_ROOT 
    save_path = user_folder + '/employee/telegram/user_session'
    session = f"{save_path}/{mobile_number}"
    
    client = TelegramClient(session, api_id, api_hash)

    try:
        await client.connect()

        in_mobile_number="+91 "+mobile_number
        
        # Check if the client is already authorized
        if not await client.is_user_authorized():
            print(in_mobile_number)

            
            await client.send_code_request(in_mobile_number)
            
            for num in range(60):
                await asyncio.sleep(2)
                print(num)

                otp,password = await check_otp_and_password_in_database(user_id, mobile_number)
                if otp is not None:
                    print(otp)
                    try:
                        await client.sign_in(in_mobile_number, otp)
                        return True, None
                    except Exception as e:
                        print("----------------------")
                        print(e)
                        if "password" in str(e).lower() and password:
                            await client.sign_in(password=password)
                            return True, None 
                        else:
                            return False, str(e)
                        
            return False, "Timeout while waiting for OTP"
        else:
            return True, None 
        
    except Exception as e:
        return False, str(e) 
    
    finally:
        await client.disconnect()

@sync_to_async
def check_otp_and_password_in_database(user_id, mobile_number):
    if TelegramAuth.objects.filter(user_id=user_id, mobile_number=mobile_number).exists():
        auth = TelegramAuth.objects.get(user_id=user_id, mobile_number=mobile_number)
        otp = auth.otp
        password = auth.password
        return otp, password
    return None, None

# @sync_to_async
# def check_otp_in_database(user_id, mobile_number):
#     print(TelegramAuth.objects.filter(user_id=user_id, mobile_number=mobile_number, otp__isnull=False).exists())
#     if TelegramAuth.objects.filter(user_id=user_id, mobile_number=mobile_number, otp__isnull=False).exists():
#         otp = TelegramAuth.objects.filter(user_id=user_id, mobile_number=mobile_number).values_list('otp', flat=True).first()
#         return otp
#     return None