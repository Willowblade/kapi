import dataclasses

from fastapi import Query, Form, APIRouter
from starlette.responses import JSONResponse

from kapi.db.borrowers import Borrower
from kapi.db.keys import Key

from kapi.db.reservations import get_reservations, add_reservation, delete_reservation

router = APIRouter()

@router.get("")
async def get_reservations_endpoint(limit: int = Query(20), offset: int = Query(0), collected: bool = Query(None), returned: bool = Query(None), building_id: str = Query(None)):
    reservations, total = get_reservations(limit=limit, offset=offset, collected=collected, returned=returned, building_id=building_id)
    return JSONResponse(content={
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [dataclasses.asdict(reservation) for reservation in reservations],
    })


@router.post("")
async def create_reservation_endpoint(
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


    borrower = Borrower(
        name=borrower_name,
        company=borrower_company,
        type=borrower_type
    )

    reservation = add_reservation(key, borrower=borrower, description=description, collection_at=collection_at, reservation_by=reservation_by, return_at=return_at)
    return {"message": "Reservation created successfully", "data": reservation }


@router.delete("/{reservation_id}")
async def delete_reservation_endpoint(reservation_id: str):
    try:
        reservation = delete_reservation(reservation_id)
        return JSONResponse(content={"message": "Reservation deleted", "data": reservation})
    except ValueError as e:
        return JSONResponse(content={"message": "Reservation not found"}, status_code=404)
