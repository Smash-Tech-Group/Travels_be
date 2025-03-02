from typing import Dict
import urllib.error, urllib.request, json
from fastapi import HTTPException

def urllib_request(
    url: str, 
    method: str=None,
    headers={},
    data=None
):
    """Helper function to build the request url using urllib"""
    
    try:
        req = urllib.request.Request(url, headers=headers, method=method, data=data)
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail=f"Request failed with status: {response.status}")
            
            data = response.read().decode('utf-8')
            return json.loads(data)

    except urllib.error.HTTPError as e:
        if e.code == 403:
            raise HTTPException(status_code=403, detail='Access forbidden: Check API key or access restrictions')
        elif e.code == 404:
            raise HTTPException(status_code=404, detail='Resource not found')
        else:
            raise HTTPException(status_code=e.code, detail=str(e))
    except urllib.error.URLError as e:
        raise HTTPException(status_code=500, detail='Network error: Unable to reach the server')
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail='Failed to decode JSON response')