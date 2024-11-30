from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

import os
from fastapi.staticfiles import StaticFiles

from kapi.util import UPLOAD_DIR, get_file_from_bucket

from kapi.api.borrowed_keys import router as borrowed_keys_router
from kapi.api.reservations import router as reservations_router
from kapi.api.buildings import router as buildings_router
from kapi.api.auth import router as auth_router

from kapi.auth.constants import API_KEY


print(API_KEY)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-API-KEY"],
)

@app.middleware("http")
async def api_key_middleware(request, call_next):
    if not (request.url.path.startswith("/auth") or request.url.path.startswith("/health") or request.url.path.startswith("/files")):
        api_key = request.headers.get("X-API-KEY")
        if api_key != API_KEY:
            return JSONResponse(content={"message": "Invalid API Key"}, status_code=403)
    response = await call_next(request)
    return response



app.include_router(borrowed_keys_router, prefix="/borrowed-keys")
app.include_router(reservations_router, prefix="/reservations")
app.include_router(buildings_router, prefix="/buildings")
app.include_router(auth_router, prefix="/auth")

# In-memory storage for form data

# Directory to save uploaded files
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files directory
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")



@app.get("/health")
async def health_check():
    return {"message": "Service is up and running"}


@app.get("/files/{filename}")
async def get_file(filename: str, api_key: str = Query('')):
    if api_key != API_KEY:
        return JSONResponse(content={"message": "Invalid API Key"}, status_code=403)
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(path=file_path)
    else:
        try:
            get_file_from_bucket(filename)
            return FileResponse(path=file_path)
        except Exception as e:
            print("Error, file was not found on OS and in bucket", e)
            return JSONResponse(content={"message": "File not found"}, status_code=404)


