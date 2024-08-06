import base64

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
import shutil
import os
from typing import List, Dict
from fastapi.staticfiles import StaticFiles

from uuid import uuid4

# from supabase import create_client, Client
#
# url: str = os.environ.get("SUPABASE_URL")
# key: str = os.environ.get("SUPABASE_KEY")
#
# supabase: Client = create_client(url, key)

app = FastAPI()

# In-memory storage for form data
data_storage: List[Dict] = []

# Directory to save uploaded files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files directory
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


def get_uuid4_filename_with_extention(filename: str) -> str:
    return str(uuid4()) + os.path.splitext(filename)[-1]


def get_image_from_base64(image: str) -> dict:
    prefix, contents = image.split(",", 1)
    datatype = prefix.split(";")[0].split(":")[1]
    if "image" in datatype:
        extention = prefix.split(";")[0].split(":image/")[1]
        return {
            "data": base64.b64decode(contents),
            "extention": extention,
        }
    if "application/octet-stream" in datatype:
        extention = ".jpeg"
        return {
            "data": base64.b64decode(contents),
            "extention": extention,
        }


def write_file(file_base64: str) -> str:
    image_from_base64 = get_image_from_base64(file_base64)
    filename = get_uuid4_filename_with_extention(f"file.{image_from_base64['extention']}")
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        buffer.write(image_from_base64["data"])
    return filename


@app.post("/upload/")
async def upload_form(
        name: str = Form(...),
        id: str = Form(...),
        image: str = Form(...),
        signature: str = Form(...)
):
    print("Received", name, id, signature[:100], image[:100])

    image_filename = write_file(image)
    signature_filename = write_file(signature)

    # Store the form data in memory
    form_data = {
        "name": name,
        "id": id,
        "image_filename": image_filename,
        "signature_filename": signature_filename,
    }
    data_storage.append(form_data)

    return {"message": "Form data uploaded successfully"}


@app.get("/health/")
async def health_check():
    return {"message": "Service is up and running"}


@app.get("/data/")
async def get_data():
    return JSONResponse(content=data_storage)


@app.get("/uploads/{filename}")
async def get_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(path=file_path)
    else:
        return JSONResponse(content={"message": "File not found"}, status_code=404)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)