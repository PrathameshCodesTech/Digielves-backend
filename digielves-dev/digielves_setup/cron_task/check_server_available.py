
import requests


def check_server():
    try:
        response = requests.get("http://192.168.1.38:8000/api/for_check/check_res/")
        if response.status_code == 200:
            print("API response: Success")
            # Do nothing if the response is successful
        elif response.status_code == 504 or response.status_code == 502:
            print("API response: Server is stopped")
        else:
            print("API response: Unknown error")
    except requests.exceptions.Timeout:
        print("API response: Timeout error - Server is stopped")
    except requests.exceptions.RequestException as e:
        print("API response:", e)


    
    




   