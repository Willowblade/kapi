import base64
import dataclasses
import datetime

from fastapi import FastAPI, Form, Query
from fastapi.responses import JSONResponse, FileResponse
import os
from fastapi.staticfiles import StaticFiles

from uuid import uuid4

from keys import is_key_borrowed, Key, Borrower, add_borrowed_key, Files, get_borrowed_key, \
    get_currently_borrowed_keys, get_all_borrow_events

app = FastAPI()

# In-memory storage for form data

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


def write_base64_file(file_base64: str) -> str:
    image_from_base64 = get_image_from_base64(file_base64)
    filename = get_uuid4_filename_with_extention(f"file.{image_from_base64['extention']}")
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        buffer.write(image_from_base64["data"])
    return filename


@app.post("/keys/borrow")
async def upload_form(
        borrower_name: str = Form(...),
        borrower_company: str = Form(None),
        borrower_type: str = Form(...),
        key_id: str = Form(...),
        key_building: str = Form(None),
        key_room: str = Form(None),
        image_base64: str = Form(...),
        signature_base64: str = Form(...)
):
    if is_key_borrowed(key_id):
        return JSONResponse(content={"message": "Key is already borrowed"}, status_code=400)

    image_filename = write_base64_file(image_base64)
    signature_filename = write_base64_file(signature_base64)

    key = Key(
        id=key_id,
        building=key_building,
        room=key_room
    )
    borrower = Borrower(
        name=borrower_name,
        company=borrower_company,
        type=borrower_type
    )

    files = Files(
        image_filename=image_filename,
        signature_filename=signature_filename
    )

    add_borrowed_key(key, borrower, files)
    # Store the form data in memory

    return {"message": "Borrowed key successfully"}

@app.post("/keys/return/{borrow_id}")
async def return_key(borrow_id: str):
    borrowed_key = get_borrowed_key(borrow_id)
    if borrowed_key is None:
        return JSONResponse(content={"message": "Key not found"}, status_code=404)

    borrowed_key.returnedAt = datetime.datetime.now().isoformat()
    borrowed_key.borrowed = False

    return JSONResponse(content={"message": "Key returned"})


@app.get("/keys/borrowed")
async def get_borrowed_keys():
    return JSONResponse(content=get_currently_borrowed_keys())



@app.get("/health/")
async def health_check():
    return {"message": "Service is up and running"}


@app.get("/keys/")
async def get_data(limit: int = Query(20), offset: int = Query(0)):
    return JSONResponse(content=get_all_borrow_events(limit, offset))


@app.get("/keys/{borrow_id}")
async def get_key(borrow_id: str):
    borrowed_key = get_borrowed_key(borrow_id)
    if borrowed_key is None:
        return JSONResponse(content={"message": "Key not found"}, status_code=404)

    return JSONResponse(content=dataclasses.asdict(borrowed_key))


@app.get("/files/{filename}")
async def get_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(path=file_path)
    else:
        return JSONResponse(content={"message": "File not found"}, status_code=404)
