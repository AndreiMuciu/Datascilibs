from fastapi import Response
from bson import json_util

def json_http_resp(content):
    return Response(content=json_util.dumps(content), media_type='application/json')