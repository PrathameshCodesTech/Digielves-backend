from django.http import JsonResponse

class PageNotFoundMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 404:
            return JsonResponse({
                "success": False,
                "status": response.status_code,
                "message": "Page not found."
            })
        return response
