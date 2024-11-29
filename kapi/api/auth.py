import os
import jwt
from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from uuid import uuid4
import time

from kapi.db.auth import user_login

router = APIRouter()

KAPI_PRIVATE_KEY = os.getenv("KAPI_PRIVATE_KEY", str(uuid4()))
API_KEY = os.getenv("KAPI_API_KEY", str(uuid4()))


class LoginModel(BaseModel):
    email: str
    password: str

@router.post("/login")
async def user_login_endpoint(
        data: LoginModel
):
    try:
        user_login(data.email, data.password)
        # login success
        jwt_token = jwt.encode({
            "api_key": API_KEY,
            "exp": int(time.time() + 60 * 60 * 24 * 7) # let's pick a week expiration since internal tool...
        }, KAPI_PRIVATE_KEY, algorithm="HS256")
        return JSONResponse(content={
            "success": True,
            "access_token": jwt_token,
        })
    except Exception as e:
        return JSONResponse(content={"success": False, "message": "Something went wrong during login", "error": str(e)}, status_code=400)

