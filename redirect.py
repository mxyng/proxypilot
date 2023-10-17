import os
from mitmproxy import http


async def request(flow: http.HTTPFlow) -> None:
  if flow.request.method == 'POST':
    flow.request.headers['X-Forwarded-Host'] = flow.request.host
    flow.request.headers['X-Forwarded-Proto'] = flow.request.scheme
    flow.request.scheme = 'http'
    flow.request.host = os.getenv('REDIRECT_HOST', '127.0.0.1')
    flow.request.port = int(os.getenv('REDIRECT_PORT', 61107))
