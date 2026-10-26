"""Keep Gradio's optional CDN iframe-resizer script off this local-only app."""
from starlette.middleware import Middleware

class LocalScripts:
    def __init__(self,app):self.app=app
    async def __call__(self,scope,receive,send):
        async def local_send(message):
            if scope['type']=='http' and message['type']=='http.response.start':
                message=dict(message)
                message['headers']=[*message.get('headers',[]),(b'content-security-policy',b"script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:")]
            await send(message)
        await self.app(scope,receive,local_send)

def local_web_options():return {'middleware':[Middleware(LocalScripts)]}
