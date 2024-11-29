from fastapi import Request, HTTPException
from kapi.auth.constants import API_KEY, KAPI_PRIVATE_KEY

class ApiKeyMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        if not request.url.path.startswith("/auth"):
            api_key = request.headers.get("X-API-KEY")
            if api_key != API_KEY:
                raise HTTPException(status_code=403, detail="Invalid API Key")
        response = await call_next(request)
        return response


