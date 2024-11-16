import base64
import dataclasses

from fastapi import FastAPI, Form, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

import os
from fastapi.staticfiles import StaticFiles

from uuid import uuid4

from keys import is_key_borrowed, Key, Borrower, add_borrowed_key, Files, get_borrowed_key, \
    return_borrowed_key, BorrowedKeyResponse, get_borrowed_keys, get_reservations, add_reservation, delete_reservation, \
    get_all_buildings, add_building

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



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


@app.post("/borrowed-keys")
async def upload_form(
        building_id: str = Form(...),
        borrower_name: str = Form(...),
        borrower_company: str = Form(None),
        borrower_type: str = Form(...),
        key_room_number: str = Form(...),
        key_type: str = Form(...),
        image_base64: str = Form(...),
        signature_base64: str = Form(...),
        reservation_id: str = Form(None),
):
    key = Key(
        room_number=key_room_number,
        building_id=building_id,
        type=key_type
    )

    if is_key_borrowed(key.id):
        return JSONResponse(content={"message": "Key is already borrowed"}, status_code=400)

    image_filename = write_base64_file(image_base64)
    signature_filename = write_base64_file(signature_base64)


    borrower = Borrower(
        name=borrower_name,
        company=borrower_company,
        type=borrower_type
    )

    files = Files(
        image_filename=image_filename,
        signature_filename=signature_filename
    )

    add_borrowed_key(key, borrower, files, reservation_id=reservation_id)
    # Store the form data in memory

    return {"message": "Borrowed key successfully"}

@app.post("/borrowed-keys/return/{borrow_id}")
async def return_key(borrow_id: str):
    try:
        return_borrowed_key(borrow_id)
        return JSONResponse(content={"message": "Key returned"})
    except ValueError as e:
        return JSONResponse(content={"message": "Borrowed key not found"}, status_code=404)



@app.get("/borrowed-keys", response_model=list[BorrowedKeyResponse])
async def get_borrowed_keys_endpoint(borrowed: bool = Query(None), limit: int = Query(20), offset: int = Query(0), building_id: str = Query(None)):
    borrowed_keys, total = get_borrowed_keys(limit=limit, offset=offset, borrowed=borrowed, building_id=building_id)
    return JSONResponse(content={
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [dataclasses.asdict(borrowed_key) for borrowed_key in borrowed_keys],
    })


@app.get("/health/")
async def health_check():
    return {"message": "Service is up and running"}


@app.get("/borrowed-keys/{borrow_id}")
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


@app.get("/reservations")
async def get_reservations_endpoint(limit: int = Query(20), offset: int = Query(0), collected: bool = Query(None), returned: bool = Query(None), building_id: str = Query(None)):
    reservations, total = get_reservations(limit=limit, offset=offset, collected=collected, returned=returned, building_id=building_id)
    return JSONResponse(content={
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [dataclasses.asdict(reservation) for reservation in reservations],
    })


@app.get("/buildings")
async def get_all_buildings_endpoint(search: str = Query(None), limit: int = Query(20), offset: int = Query(0)):
    buildings, total = get_all_buildings(search=search, limit=limit, offset=offset)
    return JSONResponse(content={
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [dataclasses.asdict(building) for building in buildings],
    })


@app.post("/buildings")
async def create_building(
        name: str = Form(...),
):
    return add_building(name)

@app.post("/reservations")
async def create_reservation(
        building_id: str = Form(...),
        key_room_number: str = Form(...),
        key_type: str = Form(...),
        description: str = Form(...),
        borrower_name: str = Form(None),
        borrower_company: str = Form(None),
        borrower_type: str = Form(...),
        # TODO should this be datetime.datetime? Check how this works in fastapi
        collection_at: str = Form(...),
        reservation_by: str = Form(...),
        return_at: str = Form(None),
):
    key = Key(
        room_number=key_room_number,
        building_id=building_id,
        type=key_type
    )

    borrower = None
    if borrower_name:
        if borrower_type is None and borrower_company is None:
            borrower_type = "owner"


        borrower = Borrower(
            name=borrower_name,
            company=borrower_company,
            type=borrower_type
        )

    reservation = add_reservation(key, borrower=borrower, description=description, collection_at=collection_at, reservation_by=reservation_by, return_at=return_at)
    return {"message": "Reservation created successfully", "data": reservation }


@app.delete("/reservations/{reservation_id}")
async def delete_reservation_endpoint(reservation_id: str):
    try:
        reservation = delete_reservation(reservation_id)
        return JSONResponse(content={"message": "Reservation deleted", "data": reservation})
    except ValueError as e:
        return JSONResponse(content={"message": "Reservation not found"}, status_code=404)