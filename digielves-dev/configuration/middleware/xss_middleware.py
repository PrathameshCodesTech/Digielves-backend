from django.utils.deprecation import MiddlewareMixin

class XSSProtectionMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response['X-XSS-Protection'] = '1; mode=block'
        return response