import json
from django.http import HttpResponse
import gzip 




    
def compress(response_data):  
    json_data = json.dumps(response_data).encode('utf-8')

    # Create a gzip compressed stream
    compressed_stream = gzip.compress(json_data)

    response = HttpResponse(status=response_data["status"], content_type='application/json')
    response.content = compressed_stream
    response['Content-Encoding'] = 'gzip'
    response['Content-Length'] = str(len(compressed_stream))
    response['X-Sensitive-Header'] = 'Hidden'
    response['Server'] = 'Hidden'
    
    return response