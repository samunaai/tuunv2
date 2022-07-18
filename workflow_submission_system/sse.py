"""
Swiped this code from this link -> https://github.com/mpetazzoni/sseclient
Here's some more content -> https://urllib3.readthedocs.io/en/stable/user-guide.html
And here too -> https://urllib3.readthedocs.io/en/latest/reference/urllib3.request.html
"""

import json
import pprint
import sseclient


def with_urllib3(url, headers):
    """Get a streaming response for the given event feed using urllib3."""
    import urllib3
    http = urllib3.PoolManager(cert_reqs = 'CERT_NONE')
    return http.request('GET', url, preload_content=False, headers=headers)

def with_requests(url, headers):
    """Get a streaming response for the given event feed using requests."""
    import requests
    return requests.get(url, stream=True, headers=headers)

# url = 'https://localhost:2746/api/v1/workflows/argo/sdk-memoize-multistep-7v4lm'
url = 'https://localhost:2746/api/v1/workflows/argo/sdk-memoize-multistep-7v4lm-return-template-3949647480/main.log'
# headers = {'Accept': 'text/event-stream'}
headers = None
response = with_urllib3(url, headers)  # or with_requests(url, headers)
print("RESPONSE ==>",type(response), type(response.data))

response_dict = json.loads(response.data.decode('utf-8'))

print( response_dict.keys() )  
print( json.dumps( response_dict,sort_keys=False, indent=4 ) ) # https://www.delftstack.com/howto/python/python-pretty-print-dictionary/

# pprint(response.data)
# client = sseclient.SSEClient(response)
# for event in client.events():
#     pprint.pprint(json.loads(event.data))
