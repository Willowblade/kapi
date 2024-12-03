import dataclasses

from fastapi import APIRouter, Query, Form
from fastapi.responses import JSONResponse

from kapi.db.borrowed_keys import Files, BorrowedKeyResponse, get_borrowed_keys, get_borrowed_key, add_borrowed_key, \
    is_key_borrowed, return_borrowed_key
from kapi.db.keys import Key
from kapi.db.borrowers import Borrower
from kapi.util import write_base64_file, upload_file_to_bucket

router = APIRouter()


@router.post("")
async def borrow_key_endpoint(
        building_id: str = Form(...),
        borrower_name: str = Form(...),
        borrower_company: str = Form(None),
        borrower_type: str = Form(...),
        borrower_email: str = Form(None),
        borrower_phone: str = Form(None),
        key_room_number: str = Form(...),
        key_type: str = Form(...),
        image_base64: str = Form(...),
        signature_base64: str = Form(...),
        reservation_id: str = Form(None),
):
    key = Key(
        room_number=key_room_number,
        building_id=building_id,
        type=key_type,
    )

    if is_key_borrowed(key.id):
        return JSONResponse(content={"message": "Key is already borrowed"}, status_code=400)

    image_filename = write_base64_file(image_base64)
    upload_file_to_bucket(image_filename)
    signature_filename = write_base64_file(signature_base64)
    upload_file_to_bucket(signature_filename)

    if borrower_email is None and borrower_phone is None:
        return JSONResponse(content={"message": "Borrower must have either an email or phone number"}, status_code=400)


    borrower = Borrower(
        name=borrower_name,
        company=borrower_company,
        type=borrower_type,
        phone=borrower_phone,
        email=borrower_email
    )

    files = Files(
        image_filename=image_filename,
        signature_filename=signature_filename
    )

    add_borrowed_key(key, borrower, files, reservation_id=reservation_id)
    # Store the form data in memory

    return {"message": "Borrowed key successfully"}

@router.post("/return/{borrow_id}")
async def return_key_endpoint(borrow_id: str):
    try:
        return_borrowed_key(borrow_id)
        return JSONResponse(content={"message": "Key returned"})
    except ValueError as e:
        return JSONResponse(content={"message": "Borrowed key not found"}, status_code=404)



@router.get("", response_model=list[BorrowedKeyResponse])
async def get_borrowed_keys_endpoint(borrowed: bool = Query(None), limit: int = Query(20), offset: int = Query(0), building_id: str = Query(None)):
    borrowed_keys, total = get_borrowed_keys(limit=limit, offset=offset, borrowed=borrowed, building_id=building_id)
    return JSONResponse(content={
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [dataclasses.asdict(borrowed_key) for borrowed_key in borrowed_keys],
    })


@router.get("/{borrow_id}")
async def get_key(borrow_id: str):
    borrowed_key = get_borrowed_key(borrow_id)
    if borrowed_key is None:
        return JSONResponse(content={"message": "Key not found"}, status_code=404)

    return JSONResponse(content=dataclasses.asdict(borrowed_key))

