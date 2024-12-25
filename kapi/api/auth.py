import jwt
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import time

from kapi.auth.auth import user_login
from kapi.auth.constants import KAPI_PRIVATE_KEY, API_KEY
from kapi.notifications import send_push_notification

router = APIRouter()


class LoginModel(BaseModel):
    email: str
    password: str


@router.post("/login")
async def user_login_endpoint(
        data: LoginModel
):
    try:
        user = user_login(data.email, data.password)
        # login success
        jwt_token = jwt.encode({
            "email": user.user.email,
            "api_key": API_KEY,
            "exp": int(time.time() + 60 * 60 * 24 * 7) # let's pick a week expiration since internal tool...
        }, KAPI_PRIVATE_KEY, algorithm="HS256")
        send_push_notification(f"User {data.email} logged in")
        return JSONResponse(content={
            "success": True,
            "access_token": jwt_token,
        })
    except Exception as e:
        return JSONResponse(content={"success": False, "message": "Something went wrong during login", "error": str(e)}, status_code=400)

