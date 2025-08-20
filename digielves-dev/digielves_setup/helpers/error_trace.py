from django.conf import settings
import traceback
from django.http import JsonResponse


def create_error_response(exception, status_code):
    
    response = {
        "success": False,
        "status": status_code,
        "message": "An error occurred."
    }
    if settings.DEBUG:
        response["errors"] = str(exception)
        response["traceback"] = traceback.format_exc()
        
    return JsonResponse(response, status=status_code)
