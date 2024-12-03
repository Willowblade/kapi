import dataclasses
from typing import Optional, Self, Tuple

from postgrest.types import CountMethod

from kapi.db.borrowers import Borrower, does_borrower_exist, add_borrower
from kapi.db.db import supabase
from kapi.db.keys import Key, does_key_exist, add_key


@dataclasses.dataclass
class KeyReservationResponse:
    id: str
    key: Key
    created_at: str
    # both extra metadata for easier querying
    collected: bool = False
    returned: bool = False
    borrower: Optional[Borrower] = None
    collection_at: Optional[str] = None
    reservation_by: Optional[str] = None
    return_at: Optional[str] = None
    borrowed_key_id: Optional[str] = None
    building_id: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    def from_supabase(cls, key_reservation: dict) -> Self:
        borrower = None

        if key_reservation.get("borrowers") is not None:
            borrower = Borrower(key_reservation["borrowers"]["name"], key_reservation["borrowers"]["type"], key_reservation["borrowers"]["company"], key_reservation["borrower_id"])

        return cls(
            id=key_reservation["id"],
            key=Key(key_reservation["keys"]["room_number"], key_reservation["keys"]["building_id"], key_reservation["keys"]["type"], key_reservation["key_id"]),
            created_at=key_reservation["created_at"],
            borrower=borrower,
            collection_at=key_reservation.get("collection_at"),
            reservation_by=key_reservation.get("reservation_by"),
            return_at=key_reservation.get("return_at"),
            borrowed_key_id=key_reservation.get("borrowed_key_id"),
            collected=key_reservation.get("collected"),
            returned=key_reservation.get("returned"),
            building_id=key_reservation.get("building_id"),
            description=key_reservation.get("description")
        )


def add_reservation(key: Key, borrower: Borrower, description: str, collection_at: str, reservation_by: str, return_at: str = None):
    if not does_key_exist(key.id):
        add_key(key)

    if borrower and not does_borrower_exist(borrower.id):
        add_borrower(borrower)

    reservation = supabase.table("key_reservations").insert([
        {
            "key_id": key.id,
            "description": description,
            "borrower_id": borrower.id if borrower is not None else None,
            "building_id": key.building_id,
            "collection_at": collection_at,
            "reservation_by": reservation_by,
            "return_at": return_at
        }
    ]).execute().data[0]

    print("Created reservation", reservation)
    return reservation


def get_reservations(limit: int = 20, offset: int = 0, collected: bool = None, returned: bool = None, building_id = None) -> Tuple[list[KeyReservationResponse], int]:
    query = supabase.table("key_reservations").select("*", "keys(*)", "borrowers(*)", count=CountMethod.exact)

    if collected is not None:
        query = query.eq("collected", collected)
    if returned is not None:
        query = query.eq("returned", returned)
    if building_id is not None:
        query = query.eq("building_id", building_id)

    query = query.order("created_at", desc=True)

    reservations = query.limit(limit).offset(offset).execute()

    return [KeyReservationResponse.from_supabase(reservation) for reservation in reservations.data], reservations.count


def does_reservation_exist(reservation_id: str):
    reservation = supabase.table("key_reservations").select("*").eq("id", reservation_id).execute()
    if len(reservation.data) == 0:
        return False
    return True


def get_open_reservation_for_key(key_id: str, borrower_id: str = None):
    # TODO also infer date for the reservation or that's a filter in the frontend?
    reservation = supabase.table("key_reservations").select("*").eq("key_id", key_id).eq("collected", False).execute()
    if len(reservation.data) == 0:
        return None
    return KeyReservationResponse.from_supabase(reservation.data[0])


def delete_reservation(reservation_id: str):
    if not does_reservation_exist(reservation_id):
        raise ValueError("Reservation does not exist")
    deleted_row = supabase.table("key_reservations").delete().eq("id", reservation_id).execute()
    return deleted_row.data[0]


def get_reservation_for_borrow_key(borrowed_key_id: str):
    reservation = supabase.table("key_reservations").select("*").eq("borrowed_key_id", borrowed_key_id).execute()
    if len(reservation.data) == 0:
        return None
    return reservation.data[0]
