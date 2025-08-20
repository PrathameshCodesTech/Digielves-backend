import time
import logging

import psutil

logger = logging.getLogger('api_hits')
class PerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss
        cpu_usage_before = psutil.cpu_percent(interval=0)  # Measure CPU usage for 0 seconds

        response = self.get_response(request)
        end_time = time.time()

        execution_time = end_time - start_time

        # Get memory usage after processing the request
        memory_after = psutil.Process().memory_info().rss
        cpu_usage_after = psutil.cpu_percent(interval=0)  # Measure CPU usage for 0 seconds
        memory_used = memory_after - memory_before
        cpu_used = cpu_usage_after - cpu_usage_before
        print("-----------------------------j")
        print(request)
        logger.info(f"API: {request} | Execution Time: {execution_time} seconds  | Memory Usage: {memory_used/1048000} | CPU Usage (in per): {cpu_used} %")  


        return response
