from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

import os
from fastapi.staticfiles import StaticFiles

from kapi.util import UPLOAD_DIR

from kapi.api.borrowed_keys import router as borrowed_keys_router
from kapi.api.reservations import router as reservations_router
from kapi.api.buildings import router as buildings_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(borrowed_keys_router, prefix="/borrowed-keys")
app.include_router(reservations_router, prefix="/reservations")
app.include_router(buildings_router, prefix="/buildings")

# In-memory storage for form data

# Directory to save uploaded files
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files directory
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")



@app.get("/health")
async def health_check():
    return {"message": "Service is up and running"}


@app.get("/files/{filename}")
async def get_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(path=file_path)
    else:
        return JSONResponse(content={"message": "File not found"}, status_code=404)


